import hou
import os
import subprocess

def fix_path(path, separator='/'):
    n_path = path.replace('\\', '/')
    if '\\\\' in n_path[2:]:
        n_path = n_path[:2] + n_path[2:].replace('\\\\', '/')
    if '//' in n_path[2:]:
        n_path = n_path[:2] + n_path[2:].replace('//', '/')
    if n_path.endswith('/'):
        n_path = n_path[:-1]
    
    return n_path.replace('/', separator)

def showMessage(message, type=hou.severityType.Message, **opts):
    hou.ui.displayMessage(message, severity=type, **opts)

def showError(message, type=hou.severityType.Error, **opts):
    hou.ui.displayMessage(message, severity=type, **opts)

def print_report(header, *body):
    report = '\n{header:=^50}\n'.format(header=header)
    for b in body:
        report += b + '\n'
    report += '='*50

    return report

def createDirAndSetVar(varname, path):
    path = fix_path(path)
    hou.putenv(varname, path)

    if not os.access(path, os.F_OK):
        os.makedirs(path)

def open_explorer(path):
    path = fix_path(os.path.dirname(path))
    
    open_path = 'start {0}'.format(path)
    subprocess.Popen(open_path, shell=True)
    return