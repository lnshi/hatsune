#
# All the constants used in the system should be presented here.
#
import select

PIPE_REQUEST_FLAG = 'REQ'

PIPE_RESPONSE_FLAG = 'RES'

COMPUTING_PID_FILE = '/var/run/hatsune/hatsune.computing.pid'

POLL_READ_ONLY = (select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR)

POLL_WRITE_ONLY = (select.POLLOUT)

POLL_READ_WRITE = (POLL_READ_ONLY | POLL_WRITE_ONLY)

# This is in milliseconds.
POLL_TIMEOUT = 1000

GENERAL_STR_SEPARATOR = '^_^'

SERVER_ADDRESS = ('127.0.0.1', 37317)

SOMAXCONN = 128

SOCKET_MSG_LEN_DELIMITER = '=M'

HELLO = 'on standby'

HELLO_RES = 'cool'

# This is in milliseconds.
HEARTBEAT = 5000

SOCKET_RES_TYPE_SUCCESS = 'S_SUCCESS'

SOCKET_RES_TYPE_FAIL = 'S_FAIL'


