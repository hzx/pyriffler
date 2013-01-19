import tornado.options
from tornado.options import define, options
import os
import os.path
import sys
import re
import shutil
from riffler import settings
from riffler.utils.gen import generateCookieSecret, generateUniqueFilename, generateTmpFilename
from riffler.utils.template import compileTemplate, processCss, prepareCss, compressCss, compressJs, compressHtml, compressCssJs
from riffler.utils.coffee import compileCoffeeModule, compileCoffee, collectCoffeeModule
from riffler.utils.sass import scssToCss
from riffler.utils.file import cat
from riffler.jasmine import buildSuite
from riffler.wendergen import WenderGen

from mutant.compiler import Compiler
from mutant.coffeegen import CoffeeGen
from mutant.coffeeformatter import CoffeeFormatter


define('task', default=None, type=str, help='select task to run')
define('debug', default=True, help='build debug version')
define('paths', default=None, type=str, help='paths where to find mutant modules, scss style folder')
define('build_path', default=None, type=str, help='dir where to put builded project')
define('wender_path', default='../wender', help='wender project dir')
define('modules', default=None, type=str, help='module names')
define('build_num', default=0, type=int, help='build number')
define('mongodb', default=None, type=str, help='mongodb connection')
define('cookie_secret', default=None, type=str, help='cookie secret for wender')
define('test_module', default=None, type=str, help='tested app.module filename')
define('test_suite', default=None, type=str, help='test_suite.module filename')

def safeRemoveFile(filename):
  if os.path.exists(filename):
    os.remove(filename)

# TODO(dem) build database schema

def generateMongodb():
  dbname = os.path.basename(options.build_path)
  user = re.sub('-', '', generateUniqueFilename())
  password = re.sub('-', '', generateUniqueFilename())

  # TODO(dem) need to create user in database

  # return 'mongodb://%s:%s@localhost:27017/%s' % (user, password, dbname)
  return 'mongodb://localhost:27017/%s' % dbname

def loadBuildStat(filePath):
  if not os.path.exists(filePath):
    return

  if os.path.isdir(filePath):
    raise Exception('build statistics file not file, actual "%s"' % filePath)

  tornado.options.parse_config_file(filePath)

def saveBuildStat(filePath):
  with open(filePath, 'w') as f:
    f.write('%s = "%s"\n' % ('mongodb', options.mongodb))
    f.write('%s = "%s"\n' % ('cookie_secret', options.cookie_secret))
    f.write('%s = %d\n' % ('build_num', options.build_num))

def generateBuildStat(filename):
  # generate mongodb connection
  if options.mongodb == None:
    options.mongodb = generateMongodb()
    # need to create
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

def getModuleCode(module):
  coffeeGen = CoffeeGen()
  coffeeFormatter = CoffeeFormatter()
  wenderGen = WenderGen()
  wenderGen.generate(module)
  coffeeGen.generate(module)
  code = coffeeFormatter.generate(module)
  return code

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
  BUILD_WENDERSERVER = os.path.join(options.build_path, 'wender/server.py')
  WENDERSERVER_TEMPLATE = os.path.join(settings.TEMPLATES_PATH, 'server.py')

  # generate static templates

  # generate handlers

  # generate urls

  # compose handlers
  handlers = []
  for module in modules:
    handlers.append({
        'module': module.name,
        'alias': '%sHandlers' % module.name,
        })

  # render server template with handlers
  compileTemplate(WENDERSERVER_TEMPLATE, BUILD_WENDERSERVER, {
      'handlers': handlers,
      'mongodb': options.mongodb,
      'debug': True,
      'cookie_secret': options.cookie_secret,
      }, {})

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
def compileApp(module, wenderCoffee):
  scssPath = os.path.abspath(os.path.normpath(
      module.path + ('/../style/%s' % module.name)))
  imgPath = os.path.abspath(os.path.normpath(
      module.path + '/../style/img'))
  imgTmpPath = os.path.join(settings.TMP_PATH, 'img')
  # generate dest filenames
  loaderTemplate = os.path.join(settings.TEMPLATES_PATH, 'app_loader.coffee')
  loaderCoffee = generateTmpFilename()
  loaderJs = generateTmpFilename()
  loaderJsMap = generateTmpFilename()
  loaderCompressJs = generateTmpFilename()
  loaderThirdPartyJs = generateTmpFilename()

  appCoffee = generateTmpFilename()
  appJs = generateTmpFilename()
  appCompressJs = generateTmpFilename()

  loaderScss = os.path.join(scssPath, 'loader.scss')
  loaderCss = generateTmpFilename()
  loaderCssMap = generateTmpFilename()
  loaderCompressCss = generateTmpFilename()

  mergedCoffee = generateTmpFilename()

  mainScss = os.path.join(scssPath, 'main.scss')
  mainCss = generateTmpFilename()
  mainCssMap = generateTmpFilename()
  mainCompressCss = generateTmpFilename()

  srcApp = os.path.join(settings.TEMPLATES_PATH, 'app.html')
  templateName = 'app-%s.html' % module.name
  destApp = generateTmpFilename()
  destCompressApp = generateTmpFilename()
  # create app loader coffee from template
  compileTemplate(loaderTemplate, loaderCoffee, {
      'css': "{{ static_url('theme/%s.css') }}" % module.name,
      'js': "{{ static_url('app/%s.js') }}" % module.name,
      'app_name': module.name,
      'message': '{{ message }}',
      }, {})

  cat([wenderCoffee, loaderCoffee], mergedCoffee)
  compileCoffee(mergedCoffee, loaderJs)

  # cat loaderJs with json2
  cat([settings.JSON2, loaderJs], loaderThirdPartyJs)

  # compile app loader coffee to js
  # compileCoffee(loaderCoffee, loaderJs)

  # compile sass style
  scssToCss(loaderScss, loaderCss)
  scssToCss(mainScss, mainCss)

  # copy img from style to tmp path
  shutil.copytree(imgPath, imgTmpPath)

  # compile mut module to appCoffee
  moduleCode = getModuleCode(module)
  with open(appCoffee, 'w') as f: f.write(moduleCode)
  # compile appCoffee to appJs
  compileCoffee(appCoffee, appJs)

  # debug(dem)
  print appCoffee

  # compress loaderCss
  # compressCssJs(loaderCss, loaderJs)
  compressCss(loaderCss, loaderCssMap, loaderCompressCss, not options.debug)

  # compress mainCss
  compressCss(mainCss, mainCssMap, mainCompressCss, not options.debug)

  if not options.debug:
    # compress loaderJs
    compressJs(loaderThirdPartyJs, loaderCssMap, loaderCompressJs, loaderJsMap)

    # compress appJs
    compressJs(appJs, '', appCompressJs, '')
  else:
    shutil.copy(loaderThirdPartyJs, loaderCompressJs)
    shutil.copy(appJs, appCompressJs)

  # create app html template
  compileTemplate(srcApp, destApp, {
      'lang': '{{ lang }}',
      'title': '{{ title }}',
      }, {
      'loader_css': loaderCompressCss,
      'loader_js': loaderCompressJs,
      })

  if not options.debug:
    # compress app-name.html
    compressHtml(destApp, destCompressApp)
  else:
    shutil.copy(destApp, destCompressApp)

  shutil.copy(destCompressApp, os.path.join(options.build_path, 'templates/%s' % templateName))
  shutil.copy(mainCompressCss, os.path.join(options.build_path, 'static/theme/%s.css' % module.name))
  shutil.copy(appCompressJs, os.path.join(options.build_path, 'static/app/%s.js' % module.name))

  # remove tmp files
  safeRemoveFile(loaderCoffee)
  safeRemoveFile(loaderJs)
  safeRemoveFile(loaderThirdPartyJs)
  safeRemoveFile(loaderJsMap)
  safeRemoveFile(loaderCompressJs)
  safeRemoveFile(mergedCoffee)
  # safeRemoveFile(appCoffee)
  safeRemoveFile(appJs)
  safeRemoveFile(loaderCss)
  safeRemoveFile(loaderCssMap)
  safeRemoveFile(loaderCompressCss)
  safeRemoveFile(mainCss)
  safeRemoveFile(mainCssMap)
  safeRemoveFile(mainCompressCss)
  safeRemoveFile(destApp)
  shutil.rmtree(imgTmpPath)

def build():
  # recreate tmp path
  if os.path.exists(settings.TMP_PATH):
    shutil.rmtree(settings.TMP_PATH)
  os.mkdir(settings.TMP_PATH)
  # recreate base structure
  statFilename = os.path.join(options.build_path, 'build')
  loadBuildStat(statFilename)
  recreateBuildPath(options.build_path)
  generateBuildStat(statFilename)

  # compile applications modules
  modules = getCompiledModules(options.modules)

  # coffeeGen = CoffeeGen()
  # coffeeFormatter = CoffeeFormatter()
  # wenderGen = WenderGen()
  # # compile mutant module to appCoffee
  # for module in modules:
  #   wenderGen.generate(module)
  #   coffeeGen.generate(module)
  #   moduleCode = coffeeFormatter.generate(module)
  #   # debug
  #   print moduleCode

  # compile wender_coffee
  wenderModule = os.path.abspath(os.path.join(
      options.wender_path, 'wender_coffee/wender.module'))
  wenderCoffee = generateTmpFilename()
  collectCoffeeModule(wenderModule, wenderCoffee)

  for module in modules:
    compileApp(module, wenderCoffee)

  os.remove(wenderCoffee)

  # generate server applications
  generateServerApps(modules)

  # shutil.rmtree(settings.TMP_PATH)

def test():
  # recreate tmp path
  if os.path.exists(settings.TMP_PATH):
    shutil.rmtree(settings.TMP_PATH)
  os.mkdir(settings.TMP_PATH)

  if os.path.exists(options.build_path):
    shutil.rmtree(options.build_path)
  os.mkdir(options.build_path)
  buildSuite(options.test_suite, options.test_module, options.build_path)

def main():
  if options.task == 'build':
    build()
  if options.task == 'test':
    test()

if __name__ == '__main__':
  tornado.options.parse_command_line()
  main()
