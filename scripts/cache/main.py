from time import strftime
from tkinter import N
import hou
import os
import importlib
import re
import json
import shutil
import datetime

from utils import main as utils
importlib.reload(utils)

from save_scene import main as save_scene
importlib.reload(save_scene)

def cache_dir():
  cache_root = hou.getenv('CACHE_PATH')

  if not cache_root:
    cache_root = hou.getenv('HIP')
    cache_root = os.path.join(cache_root, 'cache')

  cache_root = utils.fix_path(cache_root)

  return cache_root

def cache_path(mode='path'):
  node = hou.pwd()

  cache_root = node.evalParm('cache_dir')
  name = node.evalParm('cache_name')
  if node.evalParm('version_enable'):
    version = 'v{0:0>3}'.format(node.evalParm('version'))
  else:
    version = ''
  if node.evalParm('framerange_type') != 0:
    frame = '.{0:0>4}'.format(int(hou.frame()))
    frame_placeholder = '.$F4'
  else:
    frame = ''
    frame_placeholder = ''

  extension = node.evalParm('cache_ext')

  fullname_label = '{name}{frame}{ext}'.format(name=name, frame=frame_placeholder, ext=extension)

  fullname = '{name}{frame}{ext}'.format(name=name, frame=frame, ext=extension)
  fullpath = utils.fix_path(os.path.join(cache_root, name, version, fullname))


  if mode == 'path':
    return fullpath
  if mode == 'name':
    return fullname_label
  return ''

def autoversion(node, forced=False):
  if node.evalParm('version_enable') and node.evalParm('version_auto') or forced:
    cache_dir = node.evalParm('cache_dir')
    cache_name = node.evalParm('cache_name')
    path = utils.fix_path(os.path.join(cache_dir, cache_name))
    
    if not os.access(path, os.F_OK):
      node.parm('version').set(1)
      return

    versions = []

    dirs = os.listdir(path)
    for d in dirs:
      if os.path.isdir(os.path.join(path, d)):
        regex = r'v(?P<version>\d+)'
        match = re.match(regex, d)
        if match:
          versions.append(int(match.group('version')))

    if len(versions) == 0:
      node.parm('version').set(1)
      return
    
    latest_version = sorted(list(set(versions)))[-1]
    if forced:
      node.parm('version').set(latest_version)
    else:
      node.parm('version').set(latest_version+1)
    
  return

def latest_version(kwargs):
  node = kwargs['node']
  autoversion(node, forced=True)
  node.parm('reload').pressButton()
  return

def watchlist_parm_val(node_idx, parm_idx):
  node = hou.pwd()

  node_ref = hou.node(node.evalParm('watchlist_write_node{0}'.format(node_idx)))
  parm_name = node.evalParm('watchlist_write_node{0}_param{1}'.format(node_idx, parm_idx))
  
  parm_ref = node_ref.parm(parm_name)
  if not parm_ref:
    return

  has_keyframes = len(parm_ref.keyframes()) > 0
  try:
    parm_ref.expression()
    is_expression = True
  except hou.OperationFailed:
    is_expression = False

  if has_keyframes and not is_expression:
    return '<< Keyframes >>'

  if has_keyframes and is_expression:
    return parm_ref.rawValue()

  return parm_ref.evalAsString()

def watchlist_action(kwargs):
  node = kwargs['node']
  action_node_idx = kwargs['script_multiparm_index2']
  action_parm_idx = kwargs['script_multiparm_index']
  action_node = hou.node(node.evalParm('watchlist_write_node{0}'.format(action_node_idx)))

  if not action_node:
    utils.showError('Invalid node selected')
    return

  parmlist = [p for p in action_node.parms() if p.parmTemplate().type() != hou.parmTemplateType.Folder and p.parmTemplate().type() != hou.parmTemplateType.FolderSet]
  treelist = []
  for p in parmlist:
    hierarchy = list(p.containingFolders())
    hierarchy.append('{0} ({1})'.format(p.parmTemplate().label(), p.name()))
    treelist.append('/'.join(hierarchy))

  usr_in = hou.ui.selectFromTree(treelist, title='Select paramter', message='Select a parameter to watch', exclusive=True, clear_on_cancel=True)
  if len(usr_in) > 0:
    idx = treelist.index(usr_in[0])
    parm = parmlist[idx]
    action_parm = node.parm('watchlist_write_node{0}_param{1}'.format(action_node_idx, action_parm_idx))
    action_parm.set(parm.name())

  return

def watchlist_write():
  def set_string_attrib(name, value):
    if not geo.findGlobalAttrib(name):
      geo.addAttrib(hou.attribType.Global, name, '', create_local_variable=False)
    geo.setGlobalAttribValue(name, value)

  node = hou.pwd()
  parent = node.parent()
  geo = node.geometry()

  set_string_attrib('hipfile_path', parent.evalParm('hipfile_path'))
  set_string_attrib('hipfile_date', parent.evalParm('hipfile_date'))
  set_string_attrib('hipfile_project', parent.evalParm('hipfile_project'))
  set_string_attrib('hipfile_source', parent.evalParm('hipfile_source'))
  set_string_attrib('hipfile_error', parent.evalParm('hipfile_error'))

  metadata = {}
  n_watch_nodes = parent.evalParm('watchlist_write')
  for i in range(n_watch_nodes):
    w_node = parent.parm('watchlist_write_node{0}'.format(i+1)).evalAsNode()
    if not w_node:
      continue

    w_node_path = w_node.path()
    metadata[w_node_path] = {}

    n_watch_parms = parent.evalParm('watchlist_write_paramslist{0}'.format(i+1))
    for j in range(n_watch_parms):
      parm_name = parent.evalParm('watchlist_write_node{0}_param{1}'.format(i+1, j+1))
      w_parm = hou.parm('{0}/{1}'.format(w_node_path, parm_name))
      if not w_parm:
        continue

      has_keyframes = len(w_parm.keyframes()) > 0
      try:
        w_parm.expression()
        is_expression = True
      except hou.OperationFailed:
        is_expression = False

      if has_keyframes and not is_expression:
        value = {}
        for k in w_parm.keyframes():
          value[k.frame()] = k.asCode()
        display = '<< Keyframes >>'
      elif has_keyframes and is_expression:
        value = w_parm.rawValue()
        display = value
      else:
        value = w_parm.eval()
        display = w_parm.evalAsString()

      if has_keyframes and is_expression:
        expression_language = 'hscript' if w_parm.expressionLanguage() == hou.exprLanguage.Hscript else 'python'
      else:
        expression_language = ''

      v = {
        'value': value,
        'display': display,
        'is_expression': is_expression,
        'has_keyframes': has_keyframes,
        'expression_language': expression_language
      }

      metadata[w_node_path][parm_name] = v
  
  json_metadata = json.dumps(metadata)
  set_string_attrib('watchlist', json_metadata)

  return

def watchlist_read(kwargs):
  def lock_parms(val):
    for p in node.parms():
      if p.name().startswith('watchlist_read_') and '_value' in p.name():
        p.lock(val)

  node = kwargs['node']
  meta_node = node.node('METADATA')
  geo = meta_node.geometry()

  if not geo or not node.evalParm('read_cache'):
    metadata = {}
  else:
    try:
      watchlist = geo.attribValue('watchlist')
      metadata = json.loads(watchlist)
    except hou.OperationFailed:
      metadata = {}

    lock_parms(False)

    n_watch_nodes = len(metadata.keys())
    node.parm('watchlist_read').set(n_watch_nodes)

    for i, (nk, n) in enumerate(metadata.items()):
      node.parm('watchlist_read_node{0}'.format(i+1)).set(nk)
      n_watch_parms = len(n.keys())
      node.parm('watchlist_read_paramslist{0}'.format(i+1)).set(n_watch_parms)

      for j, (pk, p) in enumerate(n.items()):
        node.parm('watchlist_read_node{0}_param{1}'.format(i+1, j+1)).set(pk)
        node.parm('watchlist_read_node{0}_value{1}'.format(i+1, j+1)).set(p['display'])

    lock_parms(True)

  return

def watchlist_restore_parm(kwargs):
  node = kwargs['node']
  metadata_node = node.node('METADATA')
  geo = metadata_node.geometry()

  metadata = json.loads(geo.attribValue('watchlist'))

  w_node_idx = kwargs['script_multiparm_index2']
  w_parm_idx = kwargs['script_multiparm_index']

  w_node_parm = node.parm('watchlist_read_node{0}'.format(w_node_idx))
  w_node = w_node_parm.evalAsNode()
  
  if not w_node:
    utils.showError('Node to restore to [{}] does not exist'.format(w_node_parm.evalAsString()))
    return

  w_parm_parm = node.parm('watchlist_read_node{0}_param{1}'.format(w_node_idx, w_parm_idx))
  w_parm_name = w_parm_parm.eval()
  w_parm = w_node.parm(w_parm_name)

  if not w_parm:
    utils.showError('Parm to restore to [{0}] does not exist on node [{1}]'.format(w_parm_name, w_node_parm.evalAsString()))
    return

  parm_data = metadata[w_node.path()][w_parm_name]
  if parm_data['has_keyframes'] and parm_data['is_expression']:
    lang = hou.exprLanguage.Hscript if parm_data['expression_language'] == 'hscript' else hou.exprLanguage.Python if parm_data['expression_language'] == 'python' else ''
    if lang == '':
      utils.showError('Cannot restore parm [{0}] on node [{1}] because expression language is not correctly set'.format(w_parm_name, w_node_parm.evalAsString()))
      return
    w_parm.setExpression(parm_data['value'], language=lang)
  elif parm_data['has_keyframes'] and not parm_data['is_expression']:
    w_parm.deleteAllKeyframes()
    file_path = utils.fix_path(os.path.join(hou.getenv('SCRIPTS_PATH'), 'tmp_create_key.py'))
    for v in parm_data['value'].values():
      f = open(file_path, 'w')
      f.write(v)
      f.close()
      f = open(file_path, 'r')
      exec(f.read(), globals(), locals())
      f.close()
      w_parm.setKeyframe(locals()['hou_keyframe'])
    os.remove(file_path)
  else:
    w_parm.set(parm_data['value'])

  return

def save_backup(node):
  def generate_report(success, **kwargs):
    node.parm('hipfile_path').set('None')
    node.parm('hipfile_date').set('None')
    node.parm('hipfile_project').set('None')
    node.parm('hipfile_source').set('None')
    node.parm('hipfile_error').set('None')

    if success:
      report = utils.print_report(
        'Scene Backup Report', 
        'Status: Success', 
        'Scene File: {0}'.format(kwargs['scenefile']), 
        'Date Created: {0}'.format(kwargs['date'])
      )
      node.parm('hipfile_path').set(kwargs['scenefile'])
      node.parm('hipfile_date').set(kwargs['date'])
      node.parm('hipfile_project').set(hou.getenv('PROJECT'))
      node.parm('hipfile_source').set(hou.hipFile.basename())
    else:
      report = utils.print_report(
        'Scene Backup Report',
        'Status: Failed',
        'Error Log: {0}'.format(kwargs['error'])
      )
      hou.parm('hipfile_error').set(kwargs['error'])

    utils.showMessage(report)
    return
  
  def error_report(message, severity=hou.severityType.Error):
    utils.showError(message, severity)
    generate_report(False, error=message)

  backup_dir = hou.getenv('HOUDINI_BACKUP_DIR')
  
  if not backup_dir:
    hip_dir = hou.getenv('HIP')
    backup_dir = utils.fix_path(os.path.join(hip_dir, 'backup'))
    hou.putenv('HOUDINI_BACKUP_DIR', backup_dir)
  
  if not os.access(backup_dir, os.F_OK):
    try:
      os.makedirs(backup_dir)
    except:
      error_report('Failed to create backup directory')
      return

  bk_files = os.listdir(backup_dir)
  hou.hipFile.save()
  hou.hipFile.saveAsBackup()
  n_bk_files = os.listdir(backup_dir)

  n_bk = [f for f in n_bk_files if f not in bk_files]

  if len(n_bk) != 1:
    error_report('Unable to link backup files')
    return

  bk_file = n_bk[0]
  if not bk_file:
    error_report('Unable to link new backup file')
    return

  bk_path = utils.fix_path(os.path.join(backup_dir, bk_file))

  cache_path = node.evalParm('cache_path')
  _split = os.path.split(cache_path)
  cache_dir = utils.fix_path('/'.join(_split[0].split('/')[:-1]))
  cache_file = _split[1]
  cache_name = cache_file.split('.')[0]
  if node.evalParm('version_enable'):
    cache_version = '.v{0:0>3}'.format(node.evalParm('version'))
  else:
    cache_version = ''

  cache_hip_dir = utils.fix_path(os.path.join(cache_dir, 'cache_hips'))
  if not os.access(cache_hip_dir, os.F_OK):
    try:
      os.makedirs(cache_hip_dir)
    except:
      error_report('Failed to create directory for backup .hip files')
      return

  cache_hip_file = '{name}{version}{ext}'.format(name=cache_name, version=cache_version, ext=os.path.splitext(bk_file)[-1])
  cache_hip_path = utils.fix_path(os.path.join(cache_hip_dir, cache_hip_file))

  try:
    shutil.copy(bk_path, cache_hip_path)
  except:
    error_report('Failed to create .hip file copy')
    return

  date = datetime.datetime.now().strftime(r'%H:%M %d-%m-%y')
  generate_report(True, scenefile=cache_hip_path, date=date)

  return

def hip_actions(action):
  node = hou.pwd()
  metadata = node.node('METADATA')
  hip_file = metadata.geometry().attribValue('hipfile_path')

  if not hip_file or hip_file == '':
    return

  if not os.access(hip_file, os.F_OK):
    return

  if action == 'open':
    hou.hipFile.load(hip_file)

  if action == 'explore':
    utils.open_explorer(hip_file)

  return

def hip_restore(kwargs):
  node = kwargs['node']

  scene_data = None
  for n in hou.node('/obj').children():
    if n.type().nameComponents()[2] == 'arche_scene_data':
      scene_data = N
      break

  if not scene_data:
    utils.showError('Scene Data node not found. Scene cannot correctly restored')
    return

  if os.path.dirname(hou.hipFile.path()) == hou.getenv('SAVE_PATH'):
    message = 'Current .hip file already seems to be saved to working files directory.\n' \
      'Are you sure you want to perform this operation?'

    choice = hou.ui.displayMessage(message, buttons=('No', 'Yes'), default_choice=1, cancel_choice=0)
    if choice == 0:
      return

  try:
    metadata_src = node.node('METADATA').geometry().attribValue('hipfile_source')
  except hou.OperationFailed:
    utils.showError('Unable to find source in metadata')
    return

  regex =  r'^(?P<project>\w+)-(?P<shot>\w+)-(?P<department>\w+)-(?P<task>\w+)-(?P<full_version>v(?P<version>\d{3,}))(-(?P<description>\w+))?-(?P<user>\w+)(?P<full_extension>\.(?P<extension>\w+))$'
  match = re.match(regex, metadata_src)
  if not match:
    utils.showError('Source does not align with correct naming convention.\nUnable to restore scene correctly')
    return

  department = match.group('department')
  if not department or department == '':
    utils.showError('Unable to find department from metadata.\nReverting to "na" deparment name', severity=hou.severityType.Warning)
    department = 'na'
  
  task = match.group('task')
  if not task or task == '':
    utils.showError('Unable to find task from metadata.\nReverting to "restore" task name', severity=hou.severityType.Warning)
    task = 'restore'

  desc = 'restore'

  save_scene.save_scene(None, dept=department, task=task, desc=desc)

def onCreated(kwargs):
  node = kwargs['node']
  
  node.setColor(hou.Color(0.384, 0.184, 0.329))
  node.parm('cache_path').lock(True)
  node.parm('hip_path').lock(True)

  return

def onInputChanged(kwargs):
  # print('input')
  return

def prerender(node):
  autoversion(node.parent())
  save_backup(node.parent())
  return
    
def preframe(node):
  # print('preframe')
  return
    
def postframe(node):
  # print('postframe')
  return
    
def postwrite(node):
  # print('postwrite')
  return
    
def postrender(node):
  # print('postrender')
  return
