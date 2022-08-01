import hou
import importlib
import re
import os

from utils import main as utils
importlib.reload(utils)

def clean_name(name):
  nname = name.lower().strip()
  regex = r'\W+'
  nname = re.sub(regex, '_', nname)
  return nname

def save_scene(kwargs=None, dept=None, task=None, desc=None):
  if kwargs:
    ctrl = kwargs['ctrlclick']
  else:
    ctrl = False

  scene_data = None
  for n in hou.node('/obj').children():
    if n.type().nameComponents()[2] == 'arche_scene_data':
      scene_data = n
      break

  if scene_data is None:
    utils.showError('SceneData node not found\nPlease create one')
    return

  save_path = hou.getenv('SAVE_PATH')
  project = hou.getenv('CODE')
  scene = hou.getenv('SCENE')

  if None in [save_path, project, scene]:
    utils.showError('Local variables not found\nPlease check that the SceneData node is correctly set')
    return

  curr_scenename = hou.hipFile.basename()
  scenename_regex = r'^(?P<project>\w+)-(?P<shot>\w+)-(?P<department>\w+)-(?P<task>\w+)-(?P<full_version>v(?P<version>\d{3,}))(-(?P<description>\w+))?-(?P<user>\w+)(?P<full_extension>\.(?P<extension>\w+))$'
  scene_match = re.match(scenename_regex, curr_scenename)
  
  if scene_match:
    if not dept:
      dept = scene_match.group('department')
    if not task:
      task = scene_match.group('task')
    if not desc:
      desc = scene_match.group('description')
  
  if not dept:
    dept = ''
  if not task:
    task = ''
  if not desc:
    desc = ''

  ask_input = True
  if ctrl and len(dept) > 0 and len(task) > 0:
    ask_input = False

  if ask_input:
    repeat = True
    while repeat:
      usr_in = hou.ui.readMultiInput('Select department, task and description', ('Department', 'Task', 'Description (optional)'), buttons=('Cancel', 'OK'), default_choice=1, close_choice=0, title='Save scene', initial_contents=(dept, task, desc))

      if usr_in[0] == 0:
        return

      dept = usr_in[1][0]
      task = usr_in[1][1]
      desc = usr_in[1][2]

      if '' in [dept, task]:
        utils.showError('Department and Task fields cannot be empty')
        continue

      repeat = False

  regex = '(?P<project>{project})-(?P<shot>{shot})-(?P<department>{department})-(?P<task>{task})-v(?P<version>\d{{3,}})'.format(project=project, shot=scene, department=dept, task=task)
  versions = []

  for f in os.listdir(save_path):
    if not os.path.isdir(f):
      match = re.match(regex, f, flags=re.IGNORECASE)
      if match:
        ver = int(match.group('version'))
        versions.append(ver)
 
  if len(versions) > 0:
    last_version = sorted(versions)[-1]
    version = 'v{0:>03}'.format(last_version+1)
  else:
    version = 'v001'

  user = hou.getenv('USER').lower()
  
  scene_name_components = [project, scene, dept, task, version, desc, user]
  for i, c in enumerate(scene_name_components):
    if c and len(c) > 0:
      scene_name_components[i] = clean_name(c)
    else:
      del scene_name_components[i]

  license_dict = {
    'Commercial': 'hip',
    'Indie': 'hiplc',
    'Apprentice': 'hipnc',
    'ApprenticeHD': 'hipnc',
    'Education': 'hipnc'
  }
  lic = hou.licenseCategory().name()
  ext = license_dict[lic]

  scenename = '-'.join(scene_name_components)
  scenefile = utils.fix_path(os.path.join(save_path, '{0}.{1}'.format(scenename, ext)))

  hou.hipFile.save(scenefile)