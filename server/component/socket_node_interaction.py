import select, socket, struct, random, json

from queue import Queue, Empty

from config import constants, job

from util import utils

class SocketNodeInteraction:

  # Refer to the global 'jobs_list' which is created in server main process.
  _jobs_list = None

  # Refer to the global 'nodes_list' which is created in server main process.
  _nodes_list = None

  _server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  _server.setblocking(False)
  _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  _server.bind(constants.SERVER_ADDRESS)
  _server.listen(constants.SOMAXCONN)

  _recv_msg_queues = {}
  _send_msg_queues = {}

  _socket_poller = select.poll()
  _socket_poller.register(_server, constants.POLL_READ_ONLY)

  _fd_to_socket = {_server.fileno(): _server,}

  def _send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order).
    msg = struct.pack('>I', len(msg)) + msg.encode('utf-8')
    sock.sendall(msg)

  # Helper function to receive n bytes or return None if EOF is hit.
  def _recv_in_len(sock, n):
    data = b''
    while len(data) < n:
      packet = sock.recv(n - len(data))
      if not packet:
        return None
      data += packet
    return data

  @classmethod
  def _recv_msg(cls, sock):
    # Read message length and unpack it into an integer.
    raw_msg_len = cls._recv_in_len(sock, 4)
    if not raw_msg_len:
      return None
    msg_len = struct.unpack('>I', raw_msg_len)[0]
    return cls._recv_in_len(sock, msg_len)

  @classmethod
  def _set_job_started_time_status_by_uuid(cls, job_uuid, on_which_node):
    for job_instance in cls._jobs_list:
      if job_instance.get_job_uuid() == job_uuid:
        # Set job's started time as now, and status as 'running'.
        job_instance.set_status(job.job_status[2])

        # Add 'job started' event.
        event_started = job.JobEventsDetail(job.job_events[2], on_which_node, utils.current_milliseconds_from_epoch())
        job_instance.add_status_details(event_started)

        return

  @classmethod
  def _schedule_job(cls):
    for job_instance in cls._jobs_list:
      if not job_instance.get_scheduled_at():
        if len(cls._send_msg_queues.keys()) != 0:
          # Have active computing nodes, now, we just use the 'random' strategy.
          r = random.randint(0, len(cls._send_msg_queues.keys()) - 1)
          i = 0
          for q_k in cls._send_msg_queues.keys():
            if i == r:
              cls._send_msg_queues[q_k].put(job_instance.get_command_obj())

              # Set job's scheduled time as now, and status as 'scheduled'.
              job_instance.set_scheduled_at(utils.current_milliseconds_from_epoch())
              job_instance.set_status(job.job_status[1])

              # Add 'job scheduled' event.
              event_scheduled = job.JobEventsDetail(job.job_events[1], q_k.getpeername(),
                                                      utils.current_milliseconds_from_epoch())
              job_instance.add_status_details(event_scheduled)

              break
            i += 1

  @classmethod
  def _deal_with_res_msg(cls):
    for q_k in cls._recv_msg_queues.keys():
      while not cls._recv_msg_queues[q_k].empty():
        next_res = json.loads(cls._recv_msg_queues[q_k].get_nowait())
        for job_instance in cls._jobs_list:
          if job_instance.get_job_uuid() == next_res['uuid']:
            if next_res['res'] == constants.SOCKET_RES_TYPE_SUCCESS:
              # Job succeeded.
              job_instance.set_status(job.job_status[6])

              # Add 'job completed' event.
              event_completed = job.JobEventsDetail(job.job_events[6], q_k.getpeername(),
                                                      utils.current_milliseconds_from_epoch())
              job_instance.add_status_details(event_completed)

            elif next_res['res'] == constants.SOCKET_RES_TYPE_FAIL:
              # Job failed, need to set the error msg into the 'JobStatusDetail'
              job_instance.set_status(job.job_status[4])

              # Add 'job filed' event.
              event_failed = job.JobEventsDetail(job.job_events[4], q_k.getpeername(),
                                                  utils.current_milliseconds_from_epoch())
              job_instance.add_status_details(event_failed)

            break


  @classmethod
  def start_node_interaction_p(cls, jobs_list, nodes_list):

    cls._jobs_list = jobs_list
    cls._nodes_list = nodes_list

    while True:

      # Get new jobs in for scheduling.
      cls._schedule_job()

      # Deal with the response queues.
      cls._deal_with_res_msg()

      socket_events = cls._socket_poller.poll(constants.POLL_TIMEOUT)

      for fd, flag in socket_events:
        s = cls._fd_to_socket[fd]

        if flag & (select.POLLIN | select.POLLPRI):
          if s is cls._server:
            print('I should only come here once for every connection.')
            # A readable socket is ready to accept a connection.
            connection, client_address = s.accept()
            connection.setblocking(False)

            cls._fd_to_socket[connection.fileno()] = connection

            # New node connected, add to node list.
            cls._nodes_list[connection.fileno()] = {
              'node': connection.getpeername(),
              'from': utils.current_milliseconds_from_epoch()
            }

            cls._socket_poller.register(connection, constants.POLL_READ_ONLY)

            cls._recv_msg_queues[connection] = Queue()

          else:
            data = cls._recv_msg(s).decode('utf-8')
            if data:
              # Proceed corresponding actions according to the received data.
              print('Received %s from %s' % (data, s.getpeername()))

              if data == constants.HELLO:
                # Received heartbeat signal 'hello', then put heartbeat reply signal into waiting sending msg queue.
                cls._send_msg_queues.setdefault(s, Queue()).put(constants.HELLO_RES)
              else:
                # Or else put the received msg into the received msg queue, wait for related process dealing with.
                cls._recv_msg_queues[s].put(data)
              
              cls._socket_poller.modify(s, constants.POLL_READ_WRITE)

            else:
              # Got nothing, this is abnormal, we should just close the connection and set the node as dead.
              print('Received nothing from %s\nThis is abnormal, will set node: %s as dead.' %
                      (s.getpeername(), s.getpeername()))
              cls._socket_poller.unregister(s)

              # Here can I still get the fileno by calling 's.fileno()'?
              del cls._fd_to_socket[s.fileno()]
              del cls._nodes_list[s.fileno()]

              s.close()

              # This connections has been closed, so must delete the corresponding recv_msg_queue and send_msg_queue
              cls._recv_msg_queues.pop(s, None)
              cls._send_msg_queues.pop(s, None)

        elif flag & select.POLLOUT:
          # Socket is ready for sending data, if there is something need to be sent.
          while not cls._send_msg_queues.setdefault(s, Queue()).empty():
            next_msg = cls._send_msg_queues[s].get_nowait()
            print('Sending %s to %s' % (next_msg, s.getpeername()))

            if next_msg == constants.HELLO_RES:
              cls._send_msg(s, next_msg)
            else:
              cls._send_msg(s, json.dumps(next_msg))

              if next_msg['uuid']:
                cls._set_job_started_time_status_by_uuid(next_msg['uuid'], s.getpeername())

            if cls._send_msg_queues[s].qsize() == 0:
              #
              # Refer to the 'Issues #3' on bitbucket.
              #   Due to this issue, in 'select.POLLOUT', you only can and must modify the listener from
              #     'constants.POLL_READ_WRITE' -> 'constants.POLL_READ_ONLY'
              #   when you do send something into the socket. If you don't send anything into socket but do the above
              #   listener modification, then aftereards even you modify the listener to 'POLL_READ_WRITE' or
              #   'POLL_WRITE_ONLY', you will still not be able to get any 'select.POLLOUT' event.
              #
              #   Don't modify the listener if you have nothing need to be sent into socket, you are still be able to
              #   read from socket, so I think this is fine, but it is just so weird, hard to understand where goes
              #   wrong when I modify the listener but with sending nothing.
              #
              # This is the last element, lets modify the 'socket_poller' listener.
              cls._socket_poller.modify(s, constants.POLL_READ_ONLY)

        elif flag & select.POLLHUP:
          # A client that 'hang up', to be closed.
          print('POLLHUP received, closing ', s.getpeername())
          cls._socket_poller.unregister(s)

          # Here can I still get the fileno by calling 's.fileno()'?
          del cls._fd_to_socket[s.fileno()]
          del cls._nodes_list[s.fileno()]

          s.close()

          cls._recv_msg_queues.pop(s, None)
          cls._send_msg_queues.pop(s, None)
          
        elif flag & select.POLLERR:
          # Any event with POLLERR will cause the server must gonna close the socket
          print('Unknown exceptions happen on ', s.getpeername(), ', closing this connection.')
          cls._socket_poller.unregister(s)

          s.close()

          # Here can I still get the fileno by calling 's.fileno()'?
          del cls._fd_to_socket[s.fileno()]
          del cls._nodes_list[s.fileno()]

          cls._recv_msg_queues.pop(s, None)
          cls._send_msg_queues.pop(s, None)


