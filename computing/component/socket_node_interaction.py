import select, socket, struct, subprocess, json, shlex

from queue import Queue, Empty

from config import constants

from util import utils

class SocketNodeInteraction:

  def _send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg.encode('utf-8')
    sock.sendall(msg)

  # Helper function to recv n bytes or return None if EOF is hit
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
    # Read message length and unpack it into an integer
    raw_msg_len = cls._recv_in_len(sock, 4)
    if not raw_msg_len:
      return None
    msg_len = struct.unpack('>I', raw_msg_len)[0]
    return cls._recv_in_len(sock, msg_len)

  @classmethod
  def _executor(cls):
    while not cls._recv_msg_queue.empty():
      next_msg = json.loads(cls._recv_msg_queue.get_nowait())
      try:
        with open(next_msg['out'], 'x+') as output_file:
          with subprocess.Popen(shlex.split(next_msg['exec']),
                                  bufsize = 0, stdout = output_file, stderr = subprocess.PIPE) as proc:
            out, err = proc.communicate()

            # What is the possible value for the 'returncode'
            return_code = proc.returncode
            print('I get \'returncode\' ' + str(return_code))

            if err:
              # Got error, treat subprocess failed.
              cls._send_msg_queue.put(json.dumps({
                'uuid': next_msg['uuid'],
                'res': constants.SOCKET_RES_TYPE_FAIL,
                'err': err
              }))
            else:
              # Got no error, treat subprocess succeed.
              cls._send_msg_queue.put(json.dumps({
                'uuid': next_msg['uuid'],
                'res': constants.SOCKET_RES_TYPE_SUCCESS
              }))

      except FileExistsError as e:
        raise FileExistsError(e)

  def _connect():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(constants.SERVER_ADDRESS)

    recv_msg_queue = Queue()
    send_msg_queue = Queue()

    last_heartbeat = 0

    socket_poller = select.poll()
    socket_poller.register(client, constants.POLL_WRITE_ONLY)

    return (client, recv_msg_queue, send_msg_queue, last_heartbeat, socket_poller)

  _client, _recv_msg_queue, _send_msg_queue, _last_heartbeat, _socket_poller = _connect()

  @classmethod
  def start_socket_node_interaction_p(cls):
    while True:

      # Invoke the executor.
      cls._executor()

      socket_events = cls._socket_poller.poll(constants.POLL_TIMEOUT)
      for fd, flag in socket_events:
        if flag & select.POLLOUT:
          # Check if need to send the heartbeat signal.
          if (utils.current_milliseconds_from_epoch() - cls._last_heartbeat) >= constants.HEARTBEAT:
            print('Sending heartbeat signal: %s to server: %s' % (constants.HELLO, constants.SERVER_ADDRESS))
            cls._send_msg(cls._client, constants.HELLO)
            cls._socket_poller.modify(cls._client, constants.POLL_READ_ONLY)

          # Must when we got one HELLO check response from server, then can send out sutff other than heartbeat signal.
          if cls._last_heartbeat:
            while not cls._send_msg_queue.empty():
              next_msg = cls._send_msg_queue.get_nowait()
              print('Sending message: ' + next_msg)
              cls._send_msg(cls._client, next_msg)
              if cls._send_msg_queue.qsize() == 0:
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
                cls._socket_poller.modify(cls._client, constants.POLL_READ_ONLY)

        elif flag & (select.POLLIN | select.POLLPRI):
          data = cls._recv_msg(cls._client).decode('utf-8')
          if data:
            # Check if the data is 'constants.HELLO_RES'.
            if data == constants.HELLO_RES:
              print('Received heartbeat data from server: ' + data)
              cls._last_heartbeat = utils.current_milliseconds_from_epoch()
            else:
              print('Received non heartbeat data: ' + data)
              # Put received data into recv_msg_queue queue, waiting for related process dealing with.
              cls._recv_msg_queue.put(data)
              
            cls._socket_poller.modify(cls._client, constants.POLL_READ_WRITE)
          else:
            print('Received nothing, this is abnormal, will try to reconnect.')
            cls._socket_poller.unregister(client)
            cls._client.close()
            # Try to reconnect.
            cls._connect()

        elif flag & select.POLLHUP:
          print('POLLHUP received, will try to reconnect.')
          cls._socket_poller.unregister(cls._client)
          cls._client.close()
          # Try to reconnect.
          cls._connect()
          
        elif flag & select.POLLERR:
          print('Unknown exceptions happened, will try to reconnect.')
          cls._socket_poller.unregister(cls._client)
          cls._client.close()
          # Try to reconnect.
          cls._connect()


