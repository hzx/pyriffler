import tornado.options
from tornado.options import define, options
import os
import os.path
import sys
import re
import shutil
from riffler import settings
from riffler.utils.gen import generateCookieSecret, generateUniqueFilename
from riffler.utils.template import compileTemplate, processCss, prepareCss, compressCss, compressJs, compressHtml, compressCssJs
from riffler.utils.coffee import compileCoffeeModule, compileCoffee
from riffler.utils.sass import scssToCss

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
    options.cookie_secret = generateCookieSecret()
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

def generateServerApps(modules):
  # generate static templates

  # generate handlers

  # generate urls

  # render server template with urls

  print('TODO(dem) need code to generate server apps')

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


# compile module app
def compileApp(module):
  scssPath = os.path.abspath(os.path.normpath(
      module.path + ('/../style/%s' % module.name)))
  imgPath = os.path.abspath(os.path.normpath(
      module.path + '/../style/img'))
  imgTmpPath = os.path.join(settings.TMP_PATH, 'img')
  # generate dest filenames
  loaderTemplate = os.path.join(settings.TEMPLATES_PATH, 'app_loader.coffee')
  loaderCoffee = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  loaderJs = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  loaderJsMap = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  loaderCompressJs = os.path.join(settings.TMP_PATH, generateUniqueFilename())

  appCoffee = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  appJs = os.path.join(settings.TMP_PATH, generateUniqueFilename())

  loaderScss = os.path.join(scssPath, 'loader.scss')
  loaderCss = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  loaderCssMap = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  loaderCompressCss = os.path.join(settings.TMP_PATH, generateUniqueFilename())

  mainScss = os.path.join(scssPath, 'main.scss')
  mainCss = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  mainCssMap = os.path.join(settings.TMP_PATH, generateUniqueFilename())
  mainCompressCss = os.path.join(settings.TMP_PATH, generateUniqueFilename())

  srcApp = os.path.join(settings.TEMPLATES_PATH, 'app.html')
  templateName = 'app-%s.html' % module.name
  destApp = os.path.join(settings.TMP_PATH, templateName)
  destCompressApp = os.path.join(settings.TMP_PATH, templateName)
  # create app loader coffee from template
  compileTemplate(loaderTemplate, loaderCoffee, {
      'css': "{{ static_url('theme/%s.css') }}" % module.name,
      'js': "{{ static_url('app/%s.js') }}" % module.name,
      'app_name': module.name,
      'message': '{{ message }}',
      }, {})
  # compile app loader coffee to js
  compileCoffee(loaderCoffee, loaderJs)

  # compile sass style
  scssToCss(loaderScss, loaderCss)
  scssToCss(mainScss, mainCss)

  # copy img from style to tmp path
  shutil.copytree(imgPath, imgTmpPath)

  # compress loaderCss
  # compressCssJs(loaderCss, loaderJs)
  compressCss(loaderCss, loaderCssMap, loaderCompressCss)

  # compress loaderJs
  compressJs(loaderJs, loaderCssMap, loaderCompressJs, loaderJsMap)

  # compress mainCss
  compressCss(mainCss, mainCssMap, mainCompressCss)

  # compile mutant module to appCoffee

  # compile appCoffee to appJs

  # compress appJs

  # compressCssJs(mainCss, appJs)

  # create app html template
  compileTemplate(srcApp, destApp, {
      'lang': '{{ lang }}',
      'title': '{{ title }}',
      }, {
      'loader_css': loaderCompressCss,
      'loader_js': loaderCompressJs,
      })

  # compress app-name.html
  compressHtml(destApp, destCompressApp)

  shutil.copy(destCompressApp, os.path.join(options.build_path, 'templates/%s' % templateName))
  shutil.copy(mainCompressCss, os.path.join(options.build_path, 'static/theme/%s.css' % module.name))
  # shutil.copy(appJs, os.path.join(options.build_path, 'static/app/%s.js' % module.name))

  # remove tmp files
  os.remove(loaderCoffee)
  os.remove(loaderJs)
  # os.remove(loaderJsMap)
  os.remove(loaderCompressJs)
  # os.remove(appCoffee)
  # os.remove(appJs)
  os.remove(loaderCss)
  os.remove(loaderCssMap)
  os.remove(loaderCompressCss)
  os.remove(mainCss)
  os.remove(mainCssMap)
  os.remove(mainCompressCss)
  os.remove(destApp)
  shutil.rmtree(imgTmpPath)

def main():
  # recreate base structure
  statFilename = os.path.join(options.build_path, 'build')
  loadBuildStat(statFilename)
  recreateBuildPath(options.build_path)
  generateBuildStat(statFilename)

  # compile applications modules
  modules = getCompiledModules(options.modules)

  for module in modules:
    compileApp(module)

  # generate server applications
  generateServerApps(modules)

if __name__ == '__main__':
  tornado.options.parse_command_line()
  main()
