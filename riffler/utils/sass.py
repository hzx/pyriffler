import os.path
import sys
from riffler.utils.process import execute

def scssToCss(src, dest, importPaths=[]):
  # add import paths
  # imps = []
  # for path in importPaths:
  #   imps.append('-I')
  #   imps.append(path)
  execute(
      'sass', '--compass', '--force', '--update',
      '%s:%s' % (src, dest))
