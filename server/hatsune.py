#
# This will start the server daemon and which will be in charge of all the interaction from both 'user commands
# and 'computing daemon'.
#
import sys, os, threading

from thirdparty.daemon import Daemon

from config import constants, pipe_setup

from component.pipe_console_interaction import PipeConsoleInteraction

from component.socket_node_interaction import SocketNodeInteraction

class _Hatsune(Daemon):

  def run(self):

    # Jobs list.
    jobs_list = []

    # Computing nodes list.
    nodes_list = {}

    # Start socket interactions thread.
    socket_interaction_thread = threading.Thread(target = SocketNodeInteraction.start_node_interaction_p,
                                                  kwargs = {'jobs_list': jobs_list, 'nodes_list': nodes_list},
                                                  name = 'socket_interaction_thread')
    socket_interaction_thread.start()

    # Console end user interactions thread.
    PipeConsoleInteraction.start_concole_interaction_p(jobs_list, nodes_list)


if __name__ == '__main__':

  _hatsune = _Hatsune(constants.PID_FILE, stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr)
  
  # Will run in background.
  # _hatsune.start()

  # Will run in foreground for testing purpose.
  _hatsune.run()


