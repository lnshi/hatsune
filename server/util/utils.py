#
# All the system's util methods should go here.
#
import time, datetime

from config import constants

current_milliseconds_from_epoch = lambda: int(round(time.time() * 1000))

time_str_from_epoch_milliseconds = lambda x: datetime.datetime.fromtimestamp(x / 1000.0).strftime('%Y-%m-%d %H:%M:%S')

def remove_ch_from_str(str, ch_list):
  if str and len(str) and ch_list and len(ch_list):
    for ch in ch_list:
      str = str.replace(ch, '')
  return str

def get_readable_duration_str(begin, end):
  if begin >= end:
    return None

  left_in_seconds = int((end - begin) / 1000)

  days = int(left_in_seconds / 24 / 60 / 60)

  left_in_seconds -= days * 24 * 60 * 60
  hours = int(left_in_seconds / 60 / 60)

  left_in_seconds -= hours * 60 * 60
  minutes = int(left_in_seconds / 60)

  left_in_seconds -= minutes * 60

  return (str(days) + 'd:' if days else '') + str(hours) + 'h:' + str(minutes) + 'm:' + str(left_in_seconds) + 's'

def find_nth_out_of_quotation_mark(haystack, needle, n):
  if not haystack or not needle or n <= 0:
    return -1

  if len(haystack) < n:
    return -1

  try:
    haystack.index(needle)
  except ValueError as e:
    return -1

  temp = 0
  out_of_quotation_mark = True
  for idx, val in enumerate(haystack):
    if val in ["'", '"']:
      out_of_quotation_mark = not out_of_quotation_mark
      continue

    if out_of_quotation_mark:
      if val is needle:
        temp += 1
        if temp == n:
          return idx

  return -1

def command_str_parser(command_str):
  command_attr_arr = command_str.split(constants.GENERAL_STR_SEPARATOR)

  command_obj = {
    'type': command_attr_arr[0],
    'uuid': command_attr_arr[1]
  }

  user_command_attr_arr = command_attr_arr[2].split(' ', 1)

  command_obj['main'] = user_command_attr_arr[0]
  command_obj[user_command_attr_arr[0]] = []

  if len(user_command_attr_arr) > 0:
    i = 1
    last_occurrence_idx = -1
    while True:
      idx = find_nth_out_of_quotation_mark(user_command_attr_arr[1], ' ', i)
      if idx != -1:
        attr_item = user_command_attr_arr[1][last_occurrence_idx + 1 : idx]
        attr_item_arr = attr_item.split('=')
        if len(attr_item_arr) == 1:
          command_obj[user_command_attr_arr[0]].append({attr_item_arr[0]: None})
        else:
          command_obj[user_command_attr_arr[0]].append({attr_item_arr[0]:
                                                          remove_ch_from_str(attr_item_arr[1], ['"', "'"])})
        last_occurrence_idx = idx

      else:
        last_attr = None
        if last_occurrence_idx == -1:
          last_attr = user_command_attr_arr[1]
        else:
          last_attr = user_command_attr_arr[1][last_occurrence_idx + 1 : len(user_command_attr_arr[1])]

        last_attr_item_arr = last_attr.split('=')
        
        if len(last_attr_item_arr) == 1:
          command_obj[user_command_attr_arr[0]].append({last_attr_item_arr[0]: None})
        else:
          command_obj[user_command_attr_arr[0]].append({last_attr_item_arr[0]:
                                                          remove_ch_from_str(last_attr_item_arr[1], ['"', "'"])})

        break
        
      i += 1

  return command_obj


