import os, select, getpass, json

from config import constants, job

from util import utils

class PipeConsoleInteraction:

  # Refer to the global 'jobs_list' which is created in server main process.
  _jobs_list = None

  # Refer to the global 'nodes_list' which is created in server main process.
  _nodes_list = None
  
  # Commands poller, read commands from this pipe.
  _commands_from_poller = select.poll()
  _commands_from_pipe = os.open(constants.COMMANDS_PIPE, os.O_RDWR | os.O_NONBLOCK)
  _commands_from_poller.register(_commands_from_pipe, constants.POLL_READ_ONLY)

  # Responses poller, write responses into this pipe.
  _res_to_poller = select.poll()
  _res_to_pipe = os.open(constants.COMMANDS_RES_PIPE, os.O_RDWR | os.O_NONBLOCK)
  _res_to_poller.register(_res_to_pipe, constants.POLL_WRITE_ONLY)

  def _construct_job(command_obj):
    job_obj = {
      'status': job.job_status[0],
      'submitted_by': getpass.getuser() + '@' + os.uname()[1],
      'job_uuid': command_obj['uuid']
    }

    for item in command_obj[command_obj['main']]:
      for key in item.keys():
        if key == '-n':
          job_obj['job_id'] = item[key]
        elif key == '-e':
          job_obj['on_unit'] = item[key]
        elif key == '-o':
          job_obj['output_file'] = item[key]

    if 'output_file' not in job_obj:
      job_obj['output_file'] = '/tmp/' + job_obj['job_id'] + '.hatsune.output'
    else:
      job_obj['output_file'] = os.path.join(job_obj['output_file'], job_obj['job_id'] + '.hatsune.output')

    job_obj['queued_at'] = utils.current_milliseconds_from_epoch()

    return job_obj

  def _construct_res_str(command_id, res_type, res):
    temp_obj = {
      'res_type': res_type,
      'res': res
    }
    return constants.PIPE_RESPONSE_FLAG + constants.GENERAL_STR_SEPARATOR + command_id + \
              constants.GENERAL_STR_SEPARATOR + json.dumps(temp_obj)

  @classmethod
  def _command_dispatcher(cls, command_str):
    command_obj = utils.command_str_parser(command_str)

    if command_obj['main'] == 'submit':
      job_obj = cls._construct_job(command_obj)
      job_instance = job.Job(job_obj['job_id'], job_obj['job_uuid'], job_obj['on_unit'], job_obj['output_file'],
                              job_obj['status'], job_obj['submitted_by'], job_obj['queued_at'])

      # Job submitted.
      cls._jobs_list.append(job_instance)

      # Add 'job submitted' event.
      event_submitted = job.JobEventsDetail(job.job_events[0], 'server', utils.current_milliseconds_from_epoch())
      job_instance.add_status_details(event_submitted)

      res_str = cls._construct_res_str(command_obj['uuid'], constants.RES_TYPE_STR, 'Submit job successfully.')
      cls._pipe_write_back_res(res_str)

    elif command_obj['main'] == 'job':
      for opt in command_obj[command_obj['main']]:
        for key in opt.keys():
          if key == '-l':
            temp = []
            for job_item in cls._jobs_list:
              temp.append(job_item.get_job_json_obj())
            res_str = cls._construct_res_str(command_obj['uuid'], constants.RES_TYPE_JOB_LIST, temp)
            cls._pipe_write_back_res(res_str)
            
          elif key == '-n':
            for job_item in cls._jobs_list:
              if job_item.get_job_id() == opt[key]:
                res = {
                  job_item.get_job_id(): job_item.get_status_details()
                }
                res_str = cls._construct_res_str(command_obj['uuid'], constants.RES_TYPE_JOB_DETAIL, res)
                cls._pipe_write_back_res(res_str)
                break

    elif command_obj['main'] == 'node':
      for opt in command_obj[command_obj['main']]:
        for key in opt.keys():
          if key == '-l':
            temp = []
            for node_item in cls._nodes_list.values():
              temp.append(node_item)
            res_str = cls._construct_res_str(command_obj['uuid'], constants.RES_TYPE_NODE_LIST, temp)
            cls._pipe_write_back_res(res_str)


  @classmethod
  def _pipe_write_back_res(cls, res_str):
    while res_str:
      res_events = cls._res_to_poller.poll(constants.POLL_TIMEOUT)
      for fd, flag in res_events:
        if res_str:
          os.write(cls._res_to_pipe, res_str.encode('utf-8'))
          res_str = None
        else:
          break

  @classmethod
  def start_concole_interaction_p(cls, jobs_list, nodes_list):

    cls._jobs_list = jobs_list
    cls._nodes_list = nodes_list

    while True:
      commands_str = None
      # timeout = 1s
      commands_events = cls._commands_from_poller.poll(constants.POLL_TIMEOUT)
      for fd, flag in commands_events:
        commands_str = os.read(cls._commands_from_pipe, constants.PIPE_MAX_SIZE).decode('utf-8')
        commands_str_arr = commands_str.split('\n')
        for command_str in commands_str_arr:
          if len(command_str) != 0:
            cls._command_dispatcher(command_str)


