import os.path
import base64
from riffler.utils.process import execute


def encodeImage(filepath, compress):
  """ Returns a base64 url encoding for an image """
  filetype = filepath[-3:]
  if filetype == 'svg': filetype = 'svg+xml'
  else:
    optimizeImage(filepath, compress)
  with open(filepath, 'r') as f:
    return 'url(data:image/%s;charset=utf-8;base64,%s)' % (
        filetype, base64.b64encode(f.read()))

def optimizeImage(filepath, compress):
  """
  Optimize path filepath with optimization level.
  """
  # execute('optipng', '-o%d' % level, filepath)
  if compress:
    execute('optipng', '-zc1-9', '-zm1-9', '-zs0-3', '-f0-5', filepath)
  else:
    execute('optipng', '-o0', filepath)
