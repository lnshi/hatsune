#
# The point why has this module here:
#   Can't find a non-blocking way to monitor the sys.stdin/terminal user input then send the corresponding signal to the
#   daemonized background main process.
#
# The thinking of using this are:
#   1. Require user to enter a console.
#   2. This module will monitor any user's keyin in this console in blocking way, then send corresponding signal to the
#      daemonized background main process through the 'named pipe'.
#
import os, uuid, select, json

from cmd import Cmd

from config import constants

from util import utils

#
# I was planning to use 'select.epoll', but unfortunately it is not supported by OS X,
# the very similiar equivalent stuff on OS X is 'kqueue'.
#
# So lets just use 'select.poll'
#
# Command poller, send command into this pipe.
_command_to_poller = select.poll()

#
# If something unexpected happens, refer here:
#   http://stackoverflow.com/questions/9824806/how-come-a-file-doesnt-get-written-until-i-stop-the-program
# And this also will be a good improvement for afterwards:
#   http://www.alexonlinux.com/direct-io-in-python
#
_command_to_pipe = os.open(constants.COMMANDS_PIPE, os.O_RDWR | os.O_NONBLOCK)
_command_to_poller.register(_command_to_pipe, constants.POLL_WRITE_ONLY)

# Response pollar, get response from this pipe.
_res_from_poller = select.poll()
_res_from_pipe = os.open(constants.COMMANDS_RES_PIPE, os.O_RDWR | os.O_NONBLOCK)
_res_from_poller.register(_res_from_pipe, constants.POLL_READ_ONLY)


class _HatsuneInteractor(Cmd):

  intro = (
    '********************************************************************************\n'
    '*                          Welcome to HATSUNE console                          *\n'
    '* HATSUNE is a heterogeneous cluster job scheduling/management system written  *\n'
    '* in Python. Mainly aims at making Windows nodes can work together with others *\n'
    '* Linux/Unix nodes in a same cluster.                                          *\n'
    '*                                                                              *\n'
    '* Author: SHI XIAOYAN / LEONARD SHI / email: xiaoyan.s.sg@gmail.com            *\n'
    '*                                                                              *\n'
    '* Type ? or help or help [command] for the commands help info.                 *\n'
    '********************************************************************************\n'
  )

  prompt = '[hatsune]$ '

  exit_doc = (
    'exit    Summary:\n'
    '          Exit console.\n'
    '        Command options:\n'
    '          N/A\n'
    '        Command example:\n'
    '          exit'
  )

  quit_doc = (
    'quit    Summary:\n'
    '          Quit console, equal with the \'exit\' command.\n'
    '        Command options:\n'
    '          N/A\n'
    '        Command example:\n'
    '          quit'
  )

  submit_doc = (
    'submit  Summary:\n'
    '          Submit a job to server.\n'
    '        Command options:\n'
    '          -n=[job_id]              required\n'
    '          -e=[on-unit]             required\n'
    '          -o=[output_file_path]    optional    default: /tmp/[job_id].hatsune.output\n'
    '        Command example:\n'
    '          submit -n=job_0 -e=\'echo testimg message\' -o=/tmp\n'
    '        Note:\n'
    '          1. After submission server will execute the job automatically.\n'
    '          2. If certain option value contains space, then this option value must be in single/double quotes.\n'
    '          3. No =, \' and " are allowed in option value.\n'
    '          4. Can only specify the output file path, file name will always be \'[job_id].hatsune.output\''
  )

  job_doc = (
    'job     Summary:\n'
    '          1. Query job list.\n'
    '          2. Query a single job execution details.\n'
    '        Command options:\n'
    '          -l             optional    query job list.\n'
    '          -n=[job_id]    optional    query a single job execution details.\n'
    '        Command example:\n'
    '          job -l\n'
    '          job -n=job_0\n'
    '        Note:\n'
    '          1. If certain option value contains space, then this option value must be in single/double quotes.\n'
    '          2. No =, \' and " are allowed in option value.'
  )

  node_doc = (
    'node    Summary:\n'
    '          1. Query node list.\n'
    '        Command options:\n'
    '          -l    required    query node list.\n'
    '        Command example:\n'
    '          node -l\n'
    '        Note:\n'
    '          1. If certain option value contains space, then this option value must be in single/double quotes.\n'
    '          2. No =, \' and " are allowed in option value.'
  )

  help_info = str(exit_doc) + '\n\n' + \
              str(quit_doc) + '\n\n' + \
              str(submit_doc) + '\n\n' + \
              str(job_doc) + '\n\n' + \
              str(node_doc) + '\n\n'

  def wait_for_command_res(self, command_id):
    while command_id:
      # timeout = 1s
      res_events = _res_from_poller.poll(constants.POLL_TIMEOUT)
      for fd, flag in res_events:
        if command_id:
          #
          # Here, not that deeply understand how the 'poll' works:
          #   Lets say if I have two console instances listen the pipe, when the pipe gets some data, will any of the
          #   listeners(two console instances) receive a copy of that data?
          #
          res_str = os.read(_res_from_pipe, constants.PIPE_MAX_SIZE).decode('utf-8')
          res_arr = res_str.split(constants.GENERAL_STR_SEPARATOR)
          if command_id == res_arr[1]:
            res_obj = json.loads(res_arr[2])
            if res_obj['res_type'] == constants.RES_TYPE_STR:
              print(res_obj['res'])

            elif res_obj['res_type'] == constants.RES_TYPE_JOB_LIST:
              print(constants.RES_TPL[constants.RES_TYPE_JOB_LIST]['title'])
              for res_item in res_obj['res']:
                for ctrl_item in constants.RES_TPL[constants.RES_TYPE_JOB_LIST]['ctrl']:
                  if ctrl_item[0] == 'queued_at':
                    print(utils.time_str_from_epoch_milliseconds(res_item[ctrl_item[0]]) + '  ', end = '')
                  else:
                    if len(str(res_item[ctrl_item[0]])) > ctrl_item[1]:
                      print(res_item[ctrl_item[0]][:(ctrl_item[1] - 3)] + '...', end = '')
                    else:
                      print(res_item[ctrl_item[0]] + (' ' * (ctrl_item[1] - len(res_item[ctrl_item[0]]) + 1)), end = '')
                print('')

            elif res_obj['res_type'] == constants.RES_TYPE_JOB_DETAIL:
              print(constants.RES_TPL[constants.RES_TYPE_JOB_DETAIL]['title'])
              for job_id in res_obj['res'].keys():
                for event_item in res_obj['res'][job_id]:
                  for ctrl_item in constants.RES_TPL[constants.RES_TYPE_JOB_DETAIL]['ctrl']:
                    if ctrl_item[0] == 'job_id':
                      print(job_id + (' ' * (ctrl_item[1] - len(job_id) + 1)), end = '')
                    elif ctrl_item[0] == 'on_which_node':
                      temp_node_str = None
                      if event_item['on_which_node'] == 'server':
                        temp_node_str = event_item['on_which_node']
                      else:
                        temp_node_str = ':'.join(str(e) for e in event_item['on_which_node'])
                      print(temp_node_str + (' ' * (ctrl_item[1] - len(temp_node_str) + 1)), end = '')
                    else:
                      if ctrl_item[0] == 'when':
                        print(utils.time_str_from_epoch_milliseconds(event_item[ctrl_item[0]]) + ' ', end = '')
                      else:
                        print(event_item[ctrl_item[0]] + (' ' * (ctrl_item[1] - len(event_item[ctrl_item[0]]) + 1)),
                                end = '')
                  print('')

            elif res_obj['res_type'] == constants.RES_TYPE_NODE_LIST:
              print(constants.RES_TPL[constants.RES_TYPE_NODE_LIST]['title'])
              for res_item in res_obj['res']:
                temp_node_str = ':'.join(str(e) for e in res_item['node'])
                print(temp_node_str + (' ' * (constants.RES_TPL[constants.RES_TYPE_NODE_LIST]['ctrl'][0] -
                                                  len(temp_node_str))), end = '')
                print('Active' + (' ' * (constants.RES_TPL[constants.RES_TYPE_NODE_LIST]['ctrl'][1] -
                                            len('Active'))), end = '')
                print(utils.time_str_from_epoch_milliseconds(res_item['from']) + '      ', end = '')
                print(utils.get_readable_duration_str(res_item['from'],
                                                        utils.current_milliseconds_from_epoch()), end = '')
                print('')

            command_id = None
        else:
          break

  def send_into_pipe(self, arg):
    command_id = None
    while True:
      #
      # How do I know when timeout happens?
      #
      # timeout = 1s
      events = _command_to_poller.poll(constants.POLL_TIMEOUT)
      for fd, flag in events:
        # Don't need to check the 'fd, flag' here, coz we only registered the 'POLL_WRITE_ONLY' with one 'fd'.
        command_id = str(uuid.uuid4())
        os.write(_command_to_pipe,
                  (constants.PIPE_REQUEST_FLAG + constants.GENERAL_STR_SEPARATOR + command_id +
                    constants.GENERAL_STR_SEPARATOR + arg + '\n').encode('utf-8'))
        break

      # Modify the register for listening the command's corresponding response.
      # poller.modify(command_to_pipe, )
      if command_id:
        break

    self.wait_for_command_res(command_id)

  def default(self, arg):
    if arg:
      if arg.strip().startswith(('submit ', 'job ', 'node ')):
        self.send_into_pipe(arg)
      else:
        print('Invalid command, please refer to the related doc.\n')
        self.do_help(arg)

  def do_help(self, arg):
    if not arg:
      print(self.help_info)
    else:
      if arg.strip() == 'exit':
        print(self.exit_doc)
      elif arg.strip() == 'quit':
        print(self.quit_doc)
      elif arg.strip() == 'submit':
        print(self.submit_doc)
      elif arg.strip() == 'job':
        print(self.job_doc)
      elif arg.strip() == 'node':
        print(self.node_doc)

  def do_exit(self, arg):
    print('Exiting hatsune console...\nBye.')
    return True

  def do_quit(self, arg):
    print('Exiting hatsune console...\nBye.')
    return True


if __name__ == '__main__':
  
  _HatsuneInteractor().cmdloop()


