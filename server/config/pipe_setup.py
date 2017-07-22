import os

from config import constants

if not os.path.exists(constants.COMMANDS_PIPE):
  # What is the actual differences between 'os.mkfifo' and 'os.pipe'?
  os.mkfifo(constants.COMMANDS_PIPE)

if not os.path.exists(constants.COMMANDS_RES_PIPE):
  os.mkfifo(constants.COMMANDS_RES_PIPE)