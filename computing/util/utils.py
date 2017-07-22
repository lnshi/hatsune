#
# All the system's util methods should go here.
#
import time, datetime

current_milliseconds_from_epoch = lambda: int(round(time.time() * 1000))

time_str_from_epoch_milliseconds = lambda x: datetime.datetime.fromtimestamp(x / 1000.0).strftime('%Y-%m-%d %H:%M:%S')


