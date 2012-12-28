import tornado.options
from tornado.options import define, options
import os
import os.path
import sys
import re
import shutil
import riffler.utils

from mutant.compiler import Compiler


define('paths', default=None, type=str, help='paths where to find mutant modules, scss style folder')
define('build_path', default=None, type=str, help='dir where to put builded project')
define('build_stat_path', default=None, type=str, help='dir where to find build statistics file')
define('wender_path', default='../wender', help='wender project dir')
define('modules', default=None, type=str, help='module names')
define('build_num', default=0, type=int, help='build number')
define('cookie_secret', default=None, type=str, help='cookie secret for wender')

def loadBuildStat(filePath):
  if not os.path.exists(filePath):
    return

  if os.path.isdir(filePath):
    raise Exception('build statistics file not file, actual "%s"' % filePath)

  tornado.options.parse_config_file(filePath)

def saveBuildStat(filePath):
  with open(filePath, 'w') as f:
    f.write('%s = "%s"\n' % ('cookie_secret', options.cookie_secret))
    f.write('%s = %d\n' % ('build_num', options.build_num))

def generateBuildStat(filename):
  # generate cookie secret
  if options.cookie_secret == None:
    options.cookie_secret = riffler.utils.generateCookieSecret()
  # increment build num
  options.build_num = options.build_num + 1

  saveBuildStat(filename)

def getCompiledModules(moduleNames):
  modules = []
  # compile apps
  compiler = Compiler()
  for moduleName in re.split('\s*:\s*', moduleNames):
    module = compiler.compile(options.paths, moduleName)
    modules.append(module)
  return modules

def recreateBuildPath(path):
  path = os.path.abspath(path)
  # remove old directory path
  if os.path.exists(path):
    if not os.path.isdir(path):
      raise Exception('build_path must be directory, actual "%s"' % path)
    shutil.rmtree(path)
  # create directory
  os.mkdir(path)

  # copy wender server
  shutil.copytree(os.path.join(options.wender_path, 'wender'), os.path.join(path, 'wender'))
  shutil.copytree(os.path.join(options.wender_path, 'static'), os.path.join(path, 'static'))
  shutil.copytree(os.path.join(options.wender_path, 'templates'), os.path.join(path, 'templates'))

def generateStaticTemplates(modules):
  raise Exception('generateStaticTemplates not implemented')

def generateHandlers(modules):
  raise Exception('generateHandlers not implemented')

def generateUrls(modules):
  raise Exception('generateUrls not implemented')

def renderServerTemplate(urls):
  raise Exception('renderServerTemplate not implemented')

def generateServerApps(modules):
  # generate static templates
  generateStaticTemplates(modules)
  # generate handlers
  generateHandlers(modules)
  # generate urls
  generateUrls(modules)
  # render server template with urls
  renderServerTemplate(urls)

def printModule(module):
  print('"%s"' % (module.name))
  print('  variables:')
  for name, variable in module.variables.items():
    print('    "%s"' % name)
  print('  functions:')
  for name, func in module.functions.items():
    print('    "%s"' % name)
  print('  enums:')
  for name, enum in module.enums.items():
    print('    "%s"' % name)
  print('  structs:')
  for name, st in module.structs.items():
    print('    "%s"' % name)
  print('  classes:')
  for name, cl in module.classes.items():
    print('    "%s"' % name)

def main():
  # recreate base structure
  statFilename = os.path.join(options.build_path, 'build')
  loadBuildStat(statFilename)
  recreateBuildPath(options.build_path)
  generateBuildStat(statFilename)

  # compile applications modules
  modules = getCompiledModules(options.modules)

  # generate server applications
  generateServerApps(modules)

  # generate applications
  generateApps(modules)

if __name__ == '__main__':
  tornado.options.parse_command_line()
  main()
