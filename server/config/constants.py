#
# All the constants used in the system should be presented here.
#
import select

PID_FILE = '/var/run/hatsune/hatsune.pid'

COMMANDS_PIPE = '/var/run/hatsune/hatsune.commands.pipe'

COMMANDS_RES_PIPE = '/var/run/hatsune/hatsune.commands.res.pipe'

PIPE_REQUEST_FLAG = 'REQ'

PIPE_RESPONSE_FLAG = 'RES'

PIPE_MAX_SIZE = 1024 * 64

POLL_READ_ONLY = (select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)

POLL_WRITE_ONLY = (select.POLLOUT)

POLL_READ_WRITE = (POLL_READ_ONLY | POLL_WRITE_ONLY)

# This is in milliseconds
POLL_TIMEOUT = 1000

GENERAL_STR_SEPARATOR = '^_^'

SERVER_ADDRESS = ('127.0.0.1', 37317)

SOMAXCONN = 128

SOCKET_MSG_LEN_DELIMITER = '=M'

HELLO = 'on standby'

HELLO_RES = 'cool'

RES_TYPE_STR = 'STR'

RES_TYPE_JOB_LIST = 'JOB_LIST'

RES_TYPE_JOB_DETAIL = 'JOB_DETAIL'

RES_TYPE_NODE_LIST = 'NODE_LIST'

RES_TPL = {
  RES_TYPE_JOB_LIST: {
    'title': 'Job Id   Command                   Output File               Status    Queued At            Submitted By',
    'ctrl': [('job_id', 8), ('on_unit', 25), ('output_file', 25), ('status', 9), ('queued_at', 20),
                ('submitted_by', 20)]
  },
  RES_TYPE_JOB_DETAIL: {
    'title': 'Job Id   Event        On Which Node            When                ',
    'ctrl': [('job_id', 8), ('event', 12), ('on_which_node', 24), ('when', 20)]
  },
  RES_TYPE_NODE_LIST: {
    'title': 'Node                     Status    Be Active From           Has Been Active     ',
    'ctrl': (25, 10, 25, 20)
  }
}

SOCKET_RES_TYPE_SUCCESS = 'S_SUCCESS'

SOCKET_RES_TYPE_FAIL = 'S_FAIL'


