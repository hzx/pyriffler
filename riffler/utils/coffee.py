import os
import os.path
from riffler.utils.process import execute, executeWithOutput
from riffler.utils.file import cat


class CoffeeCompiler:

  def __init__(self):
    self.includeTable = []
    self.sourceTable = []


  def _errorNotFile(self, filename):
    print('ERROR: file not exists or not file "%s"' % filename)


  def _addSource(self, filename):
    absname = os.path.join(self.appPath, filename)
    if os.path.isfile(absname) == False:
      self._errorNotFile(absname)
      return
    if absname in self.sourceTable: return

    self.sourceTable.append(absname)


  def _addInclude(self, filename):
    absname = os.path.join(self.appPath, filename)
    if os.path.isfile(absname) == False:
      self._errorNotFile(absname)
      return
    if absname in self.includeTable: return

    self.includeTable.append(absname)

    # read file
    with open(absname, 'r') as f: lines = f.readlines()

    # parse lines
    for line in lines:
      line = line.strip()
      if len(line) == 0: continue
      command, param = line.split()
      if command == 'include': self._addInclude(param)
      if command == 'source': self._addSource(param)


  def collectCoffee(self, module, dest):
    """ Collect coffee file from many coffee files.
    filename - app.module file path
    dest - destination coffee file path
    """
    self.appPath = os.path.dirname(module)
    self._addInclude(module)

    cat(self.sourceTable, dest)


def compileCoffeeModule(module, dest):
  compiler = CoffeeCompiler()
  coffeetmp = dest + '.coffee'
  compiler.collectCoffee(module, coffeetmp)

  compileCoffee(coffeetmp, dest)
  os.remove(coffeetmp)

def compileCoffee(src, dest):
  result = executeWithOutput('coffee', '--compile', '--print', src) 
  with open(dest, 'w') as f: f.write(result)
