#!/usr/bin/env python

import os.path
import sys


TOOLS_PATH = os.path.abspath(os.path.dirname(__file__))


sys.path.append(TOOLS_PATH)
from rbtls import settings
from rbtls.utils.process import execute


"""Compile sass code to css
"""
def main():
  execute(
      'sass', '--compass', '--watch',
      '%s:%s' % (settings.STYLE_PATH, settings.CSS_PATH))
  return 0


def scssToCss():
  execute(
      'sass', '--compass', '--force', '--update',
      '%s:%s' % (settings.STYLE_PATH, settings.CSS_PATH))


if __name__ == '__main__':
  sys.exit(main())
