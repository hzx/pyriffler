#!/usr/bin/env python
# client.py - compile from coffee to js, cat with third party js libs

import os.path
import sys


TOOLS_PATH = os.path.abspath(os.path.dirname(__file__))


sys.path.append(TOOLS_PATH)
from rbtls import settings
from rbtls.utils.coffee import compileCoffee
from rbtls.utils.file import cat
import os


def main():
  thirdParty = [
      os.path.join(settings.THIRD_PARTY_PATH, 'jquery-1.7.2.js'),
      os.path.join(settings.THIRD_PARTY_PATH, 'underscore-1.3.3.js'),
      ]

  # rb-loader app
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rb-loader/rb-loader.module'),
      os.path.join(settings.JS_PATH, 'rb-loader.js'))

  # rb app
  rbJs = os.path.join(settings.JS_PATH, 'rb.js')
  rbJsTmp = rbJs + '.tmp'
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rb/rb.module'),
      rbJsTmp)
  cat(thirdParty+[rbJsTmp], rbJs)
  os.remove(rbJsTmp)

  # rbad-loader app
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rbad-loader/rbad-loader.module'),
      os.path.join(settings.JS_PATH, 'rbad-loader.js'))

  # rbad app
  rbadJs = os.path.join(settings.JS_PATH, 'rbad.js')
  rbadJsTmp = rbadJs + '.tmp'
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rbad/rbad.module'),
      rbadJsTmp)
  cat(thirdParty+[rbadJsTmp], rbadJs)
  os.remove(rbadJsTmp)

  # rbtr-loader app
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rbtr-loader/rbtr-loader.module'),
      os.path.join(settings.JS_PATH, 'rbtr-loader.js'))

  # rbtr app
  rbtrJs = os.path.join(settings.JS_PATH, 'rbtr.js')
  rbtrJsTmp = rbtrJs + '.tmp'
  compileCoffee(
      os.path.join(settings.CLIENT_PATH, 'rbtr/rbtr.module'),
      rbtrJsTmp)
  cat(thirdParty+[rbtrJsTmp], rbtrJs)
  os.remove(rbtrJsTmp)


if __name__ == '__main__':
  sys.exit(main())
