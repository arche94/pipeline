import hou
import importlib
import json
import os
import sys

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

def __unset_scene():
  variables = [
    'SCENE',
    'SCENE_PATH',
    'SAVE_PATH',
    'OUTPUT_PATH',
    'RENDER_PATH',
    'CACHE_PATH'
  ]
  for v in variables:
    hou.unsetenv(v)

def list_projects(kwargs):
  data = __read_projects()
  keys = list(data.keys())
  names = [data[k]['NAME'] for k in keys]
  
  proj_list = ['-', '-']
  for i in range(len(keys)):
    proj_list.append(keys[i])
    proj_list.append(names[i])

  return proj_list

def set_project(kwargs):
  data = __read_projects()
  node = kwargs['node']
  project_key = kwargs['script_value']

  __unset_scene()
  node.parm('scene').set('')

  if project_key == '-':
    hou.unsetenv('PROJECT')
    hou.unsetenv('CODE')
    hou.unsetenv('FPS')
    hou.unsetenv('PROJECT_PATH')
    hou.unsetenv('SCENES_PATH')
    hou.unsetenv('HDA_PATH')
    hou.unsetenv('SCRIPTS_PATH')

    hou_hda_paths = hou.getenv('HOUDINI_OTLSCAN_PATH').split(';')
    hou_hda_paths = [p for p in hou_hda_paths if '_projects' not in p]
    hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(hou_hda_paths))

    sys_scripts_path_to_del = [p for p in sys.path if '_projects' in p]
    for p in sys_scripts_path_to_del:
      sys.path.remove(p)
    
    node.cook(True)
    return

  try:
    project_data = data[project_key]
  except KeyError:
    utils.showError('Project data not found for {0}'.format(project_key))
    return

  hou.putenv('PROJECT', project_data['NAME'])
  hou.putenv('CODE', project_data['CODE'])

  fps = project_data['FPS']
  hou.putenv('FPS', str(fps))
  hou.setFps(fps)

  path = project_data['PATH']
  utils.createDirAndSetVar('PROJECT_PATH', path)

  utils.createDirAndSetVar('SCENES_PATH', utils.fix_path(os.path.join(path, config['scenes_path'])))

  project_hda_path = utils.fix_path(os.path.join(path, config['hda_path']))
  utils.createDirAndSetVar('HDA_PATH', project_hda_path)
  
  project_scripts_path = utils.fix_path(os.path.join(path, config['scripts_path']))
  utils.createDirAndSetVar('SCRIPTS_PATH', project_scripts_path)

  hda_paths = [project_hda_path, ]
  hou_hda_path = hou.getenv('HOUDINI_OTLSCAN_PATH')
  if hou_hda_path:
    hda_paths += [p for p in hou_hda_path.split(';') if '_projects' not in p]
  hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(list(set(hda_paths))))
  hou.hda.reloadAllFiles()

  sys_scripts_path_to_del = [p for p in sys.path if '_projects' in p]
  for p in sys_scripts_path_to_del:
    sys.path.remove(p)
  sys.path.append(project_scripts_path)
  
  node.cook(True)
  
def list_scenes(kwargs):
  scenes = []
  scenes_path = hou.getenv('SCENES_PATH')
  
  if scenes_path and os.access(scenes_path, os.F_OK):
    for f in os.listdir(scenes_path):
      if os.path.isdir(utils.fix_path(os.path.join(scenes_path, f))):
        scenes.append(f)
        scenes.append(f)

  return scenes

def set_scene(kwargs):
  node = kwargs['node']
  scene_key = kwargs['script_value']

  if not scene_key or len(scene_key) == 0:
    __unset_scene()
    node.cook(True)
    return

  project_path = hou.getenv('PROJECT_PATH')
  if not project_path or not os.access(project_path, os.F_OK):
    utils.showError('Project path is not accessible')
    return

  scenes_path = hou.getenv('SCENES_PATH')
  if not scenes_path:
    utils.showError('Scenes path variable is invalid')
    return

  if not os.access(scenes_path, os.F_OK):
    os.makedirs(scenes_path)

  hou.putenv('SCENE', scene_key)

  cur_scene_path = utils.fix_path(os.path.join(scenes_path, scene_key))
  if not os.access(cur_scene_path, os.F_OK):
    choice = hou.ui.displayCustomConfirmation('Scene folder "{0}" does not exist\nCreate folder now?'.format(scene_key), severity=hou.severityType.ImportantMessage, buttons=('Cancel', 'Create folder'), default_choice=1, title='Create scene folder')
    if choice == 1:
      os.makedirs(cur_scene_path)
    else:
      __unset_scene()
      node.cook(True)
      return
  hou.putenv('SCENE_PATH', cur_scene_path)

  utils.createDirAndSetVar('SAVE_PATH', utils.fix_path(os.path.join(cur_scene_path, config['scene_save_path'])))
  utils.createDirAndSetVar('OUTPUT_PATH', utils.fix_path(os.path.join(cur_scene_path, config['scene_output_path'])))
  utils.createDirAndSetVar('RENDER_PATH', utils.fix_path(os.path.join(cur_scene_path, config['scene_render_path'])))
  utils.createDirAndSetVar('CACHE_PATH', utils.fix_path(os.path.join(config['cache_path'], node.evalParm('var_code'), config['scenes_path'], scene_key)))

  node.cook(True)

def onLoaded(kwargs):
  node = kwargs['node']
  curr_scene = node.evalParm('scene')

  node.parm('project').pressButton()
  if len(curr_scene) > 0:
    node.parm('scene').set(curr_scene)
    if curr_scene in list_scenes({}):
      node.parm('scene').pressButton()

def onCreated(kwargs):
  node = kwargs['node']

  all_nodes = node.type().instances()
  if len(all_nodes) > 1:
    for n in all_nodes[1:]:
      n.destroy()
    utils.showError('A Scene Data node already exists\nOnly a single instance is allowed')
    return

  node.setName('SCENE_DATA')
  node.setUserData('nodeshape', 'circle')
  node.setColor(hou.Color(1, 0.85, 0))
  node.setGenericFlag(hou.nodeFlag.Display, False)
  node.setGenericFlag(hou.nodeFlag.Selectable, False)

  node.parm('project').set(hou.getenv('PROJECT'))
  node.parm('scene').set(hou.getenv('SCENE'))
