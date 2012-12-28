import os.path
import base64
from rbtls import settings


def encodeImage(filepath):
  """ Returns a base64 url encoding for an image """
  filetype = filepath[-3:]
  if filetype == 'svg': filetype = 'svg+xml'
  with open(filepath, 'r') as f:
    return 'url(data:image/%s;charset=utf-8;base64,%s)' % (
        filetype, base64.b64encode(f.read()))
