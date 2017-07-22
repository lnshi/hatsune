import sys

from thirdparty.daemon import Daemon

from config import constants

from component.socket_node_interaction import SocketNodeInteraction

class _HatsuneComputing(Daemon):
  def run(self):
    SocketNodeInteraction.start_socket_node_interaction_p()


if __name__ == '__main__':
  
  _hatsune_computing = _HatsuneComputing(constants.COMPUTING_PID_FILE, stdin = sys.stdin, stdout = sys.stdout,
                                          stderr = sys.stderr)
  # Will run in background.
  # _hatsune_computing.start()

  # Will run in foreground for testing purpose.
  _hatsune_computing.run()


