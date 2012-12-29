import os.path
import sys
from riffler.utils.process import execute

def scssToCss(src, dest):
  execute(
      'sass', '--compass', '--force', '--update',
      '%s:%s' % (src, dest))
