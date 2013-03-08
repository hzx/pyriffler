from riffler.utils.inifile import IniReader
from riffler import settings
import os
import os.path
import shutil
import glob

from riffler.utils.gen import generateCookieSecret, generateUniqueFilename, generateTmpFilename
from riffler.utils.template import compileTemplate, processCss, prepareCss, compressCss, compressJs, compressHtml, compressCssJs
from riffler.utils.coffee import compileCoffeeModule, compileCoffee, collectCoffeeModule
from riffler.utils.sass import scssToCss
from riffler.utils.file import cat
from riffler.wendergen import WenderGen
from riffler.server_wendergen import ServerWenderGen
from mutant import core
from mutant import common
from mutant.compiler import Compiler
from mutant.coffeegen import CoffeeGen
from mutant.coffeeformatter import CoffeeFormatter
from mutant.pygen import PyGen
from mutant.pyformatter import PyFormatter

def safeRemoveFile(filename):
  if os.path.exists(filename):
    os.remove(filename)

def genCoffeeModuleCode(module):
  coffeeGen = CoffeeGen()
  coffeeFormatter = CoffeeFormatter()
  wenderGen = WenderGen()
  wenderGen.generate(module)
  coffeeGen.generate(module)
  code = coffeeFormatter.generate(module)
  return code

class SiteConfig(object):

  def __init__(self, props):
    self.cookie_secret = props.get('cookie_secret', None)
    paths = props.get('paths', '')
    self.paths = re.split('\s*:\s*', paths) if len(paths) > 0 else []
    self.build_path = props.get('build_path', None)
    self.db_name = props.get('db_name', None)
    self.db_host = props.get('db_host', 'localhost')
    self.db_port = props.get('db_port', '27017')
    self.db_user = props.get('db_user', '')
    self.db_pass = props.get('db_pass', '')
    self.model = props.get('model', None)

    if self.cookie_secret is None: self.sayError('cookie_secret must have')
    if self.build_path is None: self.sayError('build_path must have')
    if self.db_name is None: self.sayError('db_name must have')
    if self.model is None: self.sayError('model must have')

  def sayError(self, msg):
    raise Exception('project site: %s' % msg)

class AppConfig(object):

  def __init__(self, props):
    self.name = props.get('name', None)
    self.url_load = props.get('url_load', None)
    self.access = props.get('access', 'admin')

    if self.name is None: self.sayError('name must have')
    if self.url_load is None: self.sayError('url_load must have')

  def sayError(self, msg):
    raise Exception('project app: %s' % msg)

class AppStaticConfig(object):

  def __init__(self, props):
    self.name = props.get('name', None)
    self.access = props.get('access', 'admin')

    if self.name is None: self.sayError()

  def sayError(self, msg):
    raise Exception('project app_static: %s' % msg)

class WenderBuilder(object):
  """
  From wender project create js, py project.
  """

  def __init__(self):
    self.configCreateMap = {
        'site': self.createSiteConfig,
        'app': self.createAppConfig,
        'app_static': self.createAppStaticConfig,
      }

    self.isDebug = True

  def build(self, projectFilename, isDebug):
    self.isDebug = isDebug
    self.projectPath = os.path.dirname(projectFilename)

    # parse project config
    self.parseProject(projectFilename)

    # create wender structure
    self.createWenderCarcass()

    # build server structs file
    self.structs = self.genStructs()

    # build apps
    self.buildApps()

    # build static app
    self.buildStaticApps()

    # include urls
    self.buildWenderUrls()

  def sayError(self, msg):
    raise Exception('wender_builder: %s' % msg)

  def createDb(self, projectFilename):
    # parse project config
    self.parseProject(projectFilename)
    # generate db

  def parseProject(self, projectFilename):
    # reset configs
    self.confsite = None
    self.confapps = []
    self.confappstatic = []
    # reset project urls
    self.appUrls = []
    self.staticUrls = []

    # parse project file
    projectReader = IniReader()
    sections = projectReader.read(projectFilename)
    for sectionName, sectionProps in sections:
      func = self.configCreateMap.get(sectionName, None)
      if func is None:
        raise Exception('unknown project section "%s"' % sectionName)
      func(sectionProps)

    # add wender lib to project paths
    self.confsite.paths.append(settings.WENDER_LIB_PATH)
    # add projectpath to project paths
    self.confsite.paths.append(self.projectPath)

  def createSiteConfig(self, props):
    self.confsite = SiteConfig(props)

  def createAppConfig(self, props):
    self.confapps.append(AppConfig(props))

  def createAppStaticConfig(self, props):
    self.confappstatic.append(AppStaticConfig(props))

  def buildApps(self):
    # recreate tmp path
    if os.path.exists(settings.TMP_PATH):
      shutil.rmtree(settings.TMP_PATH)
    os.mkdir(settings.TMP_PATH)

    # build wender client library
    wenderModule = os.path.join(settings.WENDER_PATH, 'client/wender_coffee/wender.module')
    wenderCoffee = generateTmpFilename()
    collectCoffeeModule(wenderModule, wenderCoffee)

    compiler = Compiler()

    # build login app

    for conf in self.confapps:
      module = compiler.compile(':'.join(self.confsite.paths), conf.name)

      # add orm structs
      mainFunc = module.functions.get('main', None)
      if mainFunc:
        ormFn = core.FunctionCallNode('wender.orm.addStructs')
        # add structs param
        ormFn.addParameter(self.structs)
        # insert to main method orm.addStructs
        mainFunc.bodyNodes.insert(0, ormFn)

      # self.genJsApp(conf, module)
      self.compileApp(module, wenderCoffee)


  def buildStaticApps(self):
    # compiler = Compiler()
    # for conf in self.confappstatic:
    #   module = compiler.compile(':'.join(self.confsite.paths), conf.name)
    #   self.genPyApp(conf, module)
    pyformatter = PyFormatter()

    for conf in self.confappstatic:
      staticPath = os.path.join(self.confsite.build_path, os.path.basename(self.projectPath))
      initFile = os.path.join(staticPath, '__init__.py')
      if not os.path.exists(staticPath):
        os.mkdir(staticPath)
        with open(initFile, 'w') as f:
          f.close
      # copy application files
      # appSrc = os.path.join(self.projectPath, '%s/%s.py' % (conf.name, conf.name))
      # appDest = os.path.join(staticPath, conf.name + '.py')
      # shutil.copy(appSrc, appDest)
      pySrc = os.path.join(self.projectPath, '%s/*.py' % conf.name)
      for filename in glob.glob(pySrc):
        shutil.copy(filename, staticPath)

      # copy templates
      templateDest = os.path.join(self.confsite.build_path, 'templates/%s/' % conf.name)
      if not os.path.exists(templateDest): os.mkdir(templateDest)
      templateSrc = os.path.join(self.projectPath, '%s/templates/*.html' % conf.name)
      for filename in glob.glob(templateSrc):
        shutil.copy(filename, templateDest)

      # add structs.py
      vaStructs = core.VariableNode([common.Token(0, 'var', 'var')], 'structs')
      vaStructs.body = self.structs
      pyformatter.savePyCode(
          pyformatter.genVariable(vaStructs),
          os.path.join(self.confsite.build_path, 'wender/structs.py')
          )


  def genStructs(self):
    compiler = Compiler()
    module = compiler.compile(':'.join(self.confsite.paths), self.confsite.model)
    wendergen = WenderGen()
    structs = wendergen.createMetaStructs(module)
    return structs

  def buildWenderUrls(self):
    self.createPyServer()

  def genJsApp(self, conf, module):
    # wendergen = WenderGen()
    # gen = CoffeeGen()
    # formatter = CoffeeFormatter()

    # wendergen.generate(module)
    # wendergen.flushUrls(self.appUrls)
    # gen.generate(module)

    # coffeecode = formatter.generate(module)
    pass

  # compile module app
  def compileApp(self, module, wenderCoffee):
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
    moduleCode = genCoffeeModuleCode(module)
    with open(appCoffee, 'w') as f: f.write(moduleCode)
    # compile appCoffee to appJs
    compileCoffee(appCoffee, appJs)

    # debug(dem)
    print appCoffee

    # compress loaderCss
    # compressCssJs(loaderCss, loaderJs)
    compressCss(loaderCss, loaderCssMap, loaderCompressCss, not self.isDebug)

    # compress mainCss
    compressCss(mainCss, mainCssMap, mainCompressCss, not self.isDebug)

    if not self.isDebug:
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

    if not self.isDebug:
      # compress app-name.html
      compressHtml(destApp, destCompressApp)
    else:
      shutil.copy(destApp, destCompressApp)

    shutil.copy(destCompressApp, os.path.join(self.confsite.build_path, 'templates/%s' % templateName))
    shutil.copy(mainCompressCss, os.path.join(self.confsite.build_path, 'static/theme/%s.css' % module.name))
    shutil.copy(appCompressJs, os.path.join(self.confsite.build_path, 'static/app/%s.js' % module.name))

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



  def genCoffeeModuleCode(self, module):
    coffeeGen = CoffeeGen()
    coffeeFormatter = CoffeeFormatter()
    wenderGen = WenderGen()
    wenderGen.generate(module)
    coffeeGen.generate(module)
    code = coffeeFormatter.generate(module)
    return code



  def genPyApp(self, conf, module):
    wendergen = ServerWenderGen()
    gen = PyGen()
    formatter = PyFormatter()

    # wendergen.generate(conf.access, module)
    # wendergen.flushUrls(self.staticUrls)
    gen.generate(module)

    return formatter.generate(
        self.confsite.build_path,
        os.path.basename(self.confsite.build_path),
        module
      )

  def createWenderCarcass(self):
    # remove old path
    if os.path.exists(self.confsite.build_path):
      if not os.path.isdir(self.confsite.build_path):
        self.sayError('build_path must be directory "%s"' % self.confsite.build_path)
      shutil.rmtree(self.confsite.build_path)

    # create directory
    os.mkdir(self.confsite.build_path)

    # copy wender server carcass
    shutil.copytree(
        os.path.join(settings.WENDER_PATH, 'server/wender'),
        os.path.join(self.confsite.build_path, 'wender')
      )
    shutil.copytree(
        os.path.join(settings.WENDER_PATH, 'server/static'),
        os.path.join(self.confsite.build_path, 'static')
      )
    shutil.copytree(
        os.path.join(settings.WENDER_PATH, 'server/templates'),
        os.path.join(self.confsite.build_path, 'templates')
      )
    shutil.copy(
        os.path.join(settings.WENDER_PATH, 'server/run.sh'),
        self.confsite.build_path
      )
    # create simlink to static directory
    projectName = os.path.basename(self.projectPath)
    projectParentPath = os.path.dirname(self.projectPath)
    os.symlink(
        os.path.join(projectParentPath, '%s_static/img' % projectName),
        os.path.join(self.confsite.build_path, 'static/img')
        )

  def genMongodbConnection(self):
    if len(self.confsite.db_user) > 0:
      if len(self.confsite.db_pass) > 0:
        return 'mongodb://%s:%s@%s:%s/%s' % (
            self.confsite.db_user,
            self.confsite.db_pass,
            self.confsite.db_host,
            self.confsite.db_port,
            self.confsite.db_name
          )
      else:
        return 'mongodb://%s@%s:%s/%s' % (
            self.confsite.db_user,
            self.confsite.db_host,
            self.confsite.db_port,
            self.confsite.db_name
          )
    return 'mongodb://%s:%s/%s' % (
        self.confsite.db_host,
        self.confsite.db_port,
        self.confsite.db_name
      )

  def createPyServer(self):
    serverTemplate = os.path.join(settings.WENDER_PATH, 'server/server.py')
    serverDest = os.path.join(self.confsite.build_path, 'wender/server.py')

    handlers = []
    prefix = os.path.basename(self.projectPath)
    for conf in self.confappstatic:
      handlers.append({
          'module': prefix + '.' + conf.name,
          'alias': '%sHandlers' % conf.name,
          })

    compileTemplate(serverTemplate, serverDest, {
        'handlers': handlers,
        'db_host': self.confsite.db_host,
        'db_port': self.confsite.db_port,
        'db_name': self.confsite.db_name,
        'db_user': self.confsite.db_user,
        'db_pass': self.confsite.db_pass,
        'debug': self.isDebug,
        'cookie_secret': self.confsite.cookie_secret,
      }, {})
