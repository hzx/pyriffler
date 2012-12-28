#!/usr/bin/env python

import os.path
import sys

TOOLS_PATH = os.path.abspath(os.path.dirname(__file__))

sys.path.append(TOOLS_PATH)
import os
from rbtls import settings
from rbtls.utils.template import prepareCss, compressCss, compressJs
from rbtls.utils.process import execute
import glob
from style import scssToCss

def getJsMapName(filename):
  name, ext = os.path.splitext(filename)
  return os.path.join(settings.JS_PATH, '%s-js-map.js' % name)

def getCssMapName(filename):
  name, ext = os.path.splitext(filename)
  return os.path.join(settings.JS_PATH, '%s-css-map.js' % name)

def compressCssJs(cssFilename, jsFilename):
  cssPath = os.path.join(settings.CSS_PATH, cssFilename)
  jsPath = os.path.join(settings.JS_PATH, jsFilename)

  cssMap = getCssMapName(jsFilename)
  jsMap = getJsMapName(jsFilename)

  # create tmp js file
  jsTmp = jsPath + '.tmp'

  if os.path.exists(jsTmp): os.remove(jsTmp)

  prepareCss(cssPath)
  compressCss(cssPath, cssMap, cssPath)
  compressJs(jsPath, cssMap, jsTmp, jsMap)

  os.rename(jsTmp, jsPath)

"""Compile css and js files
"""
def main():
  # force remove old css files
  for filename in glob.glob(settings.CSS_PATH + '/*.css'):
    os.remove(filename)

  # generate css files
  scssToCss()

  # from coffeescript build.py

  # TODO(dem) from rb to rb-loader give js-name-map
  compressCssJs('rb.css', 'rb.js')
  compressCssJs('rb-loader.css', 'rb-loader.js')

  compressCssJs('rbtr.css', 'rbtr.js')
  compressCssJs('rbtr-loader.css', 'rbtr-loader.js')

  compressCssJs('rbad.css', 'rbad.js')
  compressCssJs('rbad-loader.css', 'rbad-loader.js')

if __name__ == '__main__':
  main()
