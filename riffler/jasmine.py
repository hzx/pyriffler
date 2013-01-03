from riffler import settings
from riffler.utils.coffee import compileCoffeeModule
from riffler.utils.template import compileTemplate
import shutil
import os.path


def buildSuite(src_suite, src_module, dest):
  """
  Build jasmine suite.
  Params:
    src - src test.module
    dest - desination build path
  """
  dest_module = os.path.abspath(os.path.normpath(dest + '/module.js'))
  dest_suite = os.path.abspath(os.path.normpath(dest + '/test.js'))
  # copy third_party jasmine folder
  shutil.copytree(
      os.path.join(settings.THIRD_PARTY_PATH, 'jasmine'),
      os.path.join(dest, 'jasmine'))
  # copy jasmine_suite.html template
  compileTemplate(
      os.path.join(settings.TEMPLATES_PATH, 'jasmine_suite.html'),
      os.path.normpath(dest + '/suite.html'),
      {}, {})
  # compile coffee module
  compileCoffeeModule(os.path.abspath(src_module), dest_module)
  # compile coffee test suite
  compileCoffeeModule(os.path.abspath(src_suite), dest_suite)
