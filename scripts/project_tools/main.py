import hou
import os
import importlib
import json

from utils import main as utils
importlib.reload(utils)

pip_config_file = 'Y:/pipeline/data/config.json'
with open(pip_config_file, 'r') as config_file:
  try:
    config = json.load(config_file)
  except ValueError:
    utils.showError('Error reading pipeline configuration file')

projects = config['projects_info']

def __read_projects():
  with open(projects, 'r') as projects_file:
    if os.path.exists(projects) and os.stat(projects).st_size > 0:
      try:
        data = json.load(projects_file)
      except ValueError:
        utils.showError('Error reading projects file')
    else:
      data = {}
  
  return data

def __dump_projects(data):
  with open(projects, 'w') as projects_file:
      json.dump(data, projects_file, sort_keys=True, indent=2)

def manage_projects():
  action = hou.ui.displayMessage('Select an action', buttons=('Add', 'Remove', 'Details', 'Cancel'), default_choice=3, title='Manage projects')
  if action == 0:
    add_project()
  elif action == 1:
    remove_project()
  elif action == 2:
    details_project()
    
def add_project():
  data = __read_projects()

  repeat = True
  while repeat:
    _path = hou.ui.selectFile(title='Select project folder', file_type=hou.fileType.Directory)
    project_path = utils.fix_path(os.path.dirname(_path))
    
    if len(project_path) == 0:
      return

    
    if project_path in [utils.fix_path(v['PATH']) for v in data.values()]:
      utils.showError('Path is already used by project {0}\nPlease select a different path'.format([k for k in data.keys() if utils.fix_path(data[k]['PATH']) == project_path][0]))
      repeat = True
      continue

    repeat = False

  _project_name = 'New Project'
  _project_code = project_path.split('/')[-1]
  _project_fps = '24'

  project_name = None
  project_code = None
  project_fps = None
  
  repeat = True
  while repeat:
    proj_inputs = hou.ui.readMultiInput(message='Enter project data', input_labels=('Project Name', 'Project Code', 'FPS'), buttons=('Cancel', 'Create'), initial_contents=(_project_name, _project_code, _project_fps), default_choice=1, close_choice=0)
    result, _project_data = proj_inputs[0], proj_inputs[1]

    if result == 0:
      return

    _project_name = _project_data[0]
    _project_code = _project_data[1]
    _project_fps = _project_data[2]

    if len(_project_name) == 0 or len(_project_code) == 0 or len(_project_fps) == 0:
      utils.showError('Fill in all the required fields')
      continue
    
    project_name = _project_name
    project_code = _project_code
    try:
      project_fps = int(_project_fps)
    except ValueError:
      utils.showError('FPS needs to be an integer value')
      continue

    if project_code in data.keys():
      utils.showError('Project {0} already exists'.format(project_code))
      continue
    
    if project_name in [v['NAME'] for v in data.values()]:
      utils.showError('Project name already used by {0}\nPlease type in another name'.format([k for k in data.keys() if data[k]['NAME'] == project_name][0]))
      continue

    repeat = False

  if project_name and project_code and project_fps:
    project_data = {
      'NAME': project_name,
      'CODE': project_code,
      'PATH': project_path,
      'FPS': project_fps
    }
    data[project_code] = project_data

    __dump_projects(data)

    utils.showMessage('Project {0} created successfully'.format(project_code))
  else:
    utils.showError('Project creation exited unexpectedly')

def remove_project():
  data = __read_projects()

  project_names = [p['NAME'] for p in data.values()]
  selection = hou.ui.selectFromList(project_names, message='Select projects to remove', title='Remove project', column_header='Projects')
  
  if len(selection) == 0:
    return

  to_del = [k for k in data if data[k]['NAME'] in [project_names[i] for i in selection]]
  
  for p in to_del:
    del data[p]

  __dump_projects(data)
  utils.showMessage('Projects successfully removed\n\n{0}'.format('\n'.join(to_del)))

def details_project():
  data = __read_projects()

  project_names = [p['NAME'] for p in data.values()]
  selection = hou.ui.selectFromList(project_names, message='Select project to show details', title='Project details', exclusive=True, column_header='Projects')

  if len(selection) == 0:
    return
  
  # print(selection[0])

  project = data[[p for p in data if data[p]['NAME'] == project_names[selection[0]]][0]]
  
  header = 'Project details: {0}'.format(project['NAME'])
  body = []
  for pk, pv in project.items():
    body.append('{key}: {value}'.format(key=pk, value=pv))

  utils.showMessage(utils.print_report(header, *body))
