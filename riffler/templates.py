#!/usr/bin/env python

import sys
import os.path


TOOLS_PATH = os.path.abspath(os.path.dirname(__file__))


sys.path.append(TOOLS_PATH)
from rbtls.utils.template import compileTemplate, compressHtml, compressXml
from rbtls import settings
import glob


"""Create application templates

Inline css and js loader into html template
for applications:
  rb - rubear
  rbtr - rubear tracker
  rbad - rubear admin
"""
def main():
  # create rb template
  # TODO(dem) fix ERROR PT+Serif
  rbParams = {
      'head': '<link href="http://fonts.googleapis.com/css?family=PT+Serif:400,700&subset=latin,cyrillic" rel="stylesheet" type="text/css">',
      'title': '{{ title }}',
      }
  rbFiles = {
      'css': os.path.join(settings.CSS_PATH, 'rb-loader.css'),
      'js': os.path.join(settings.JS_PATH, 'rb-loader.js'),
      }
  rbHtml = os.path.join(settings.TEMPLATE_PATH, 'rb-app.html')
  compileTemplate(\
      os.path.join(settings.SRC_TEMPLATE_PATH, 'app.html'),\
      rbHtml,\
      rbParams, rbFiles)
  compressHtml(rbHtml, rbHtml)

  # create rbad - admin template
  rbadParams = {
      'head': '',
      'title': '{{ title }}',
      }
  rbadFiles = {
      'css': os.path.join(settings.CSS_PATH, 'rbad-loader.css'),
      'js': os.path.join(settings.JS_PATH, 'rbad-loader.js'),
      }
  rbadHtml = os.path.join(settings.TEMPLATE_PATH, 'rbad-app.html')
  compileTemplate(\
      os.path.join(settings.SRC_TEMPLATE_PATH, 'app.html'),\
      rbadHtml,\
      rbadParams, rbadFiles)
  compressHtml(rbadHtml, rbadHtml)

  # create rbtr - tracker template
  rbtrParams = {
      'head': '',
      'title': '{{ title }}',
      }
  rbtrFiles = {
      'css': os.path.join(settings.CSS_PATH, 'rbtr-loader.css'),
      'js': os.path.join(settings.JS_PATH, 'rbtr-loader.js'),
      }
  rbtrHtml = os.path.join(settings.TEMPLATE_PATH, 'rbtr-app.html')
  compileTemplate(\
      os.path.join(settings.SRC_TEMPLATE_PATH, 'app.html'),\
      rbtrHtml,\
      rbtrParams, rbtrFiles)
  compressHtml(rbtrHtml, rbtrHtml)

  # compress html
  for filename in glob.glob(settings.SRC_TEMPLATE_PATH + '/*.html'):
    destTemplate = os.path.join(settings.TEMPLATE_PATH, os.path.basename(filename))
    compressHtml(filename, destTemplate)

  for filename in glob.glob(settings.SRC_TEMPLATE_PATH + '/*.xml'):
    destTemplate = os.path.join(settings.TEMPLATE_PATH, os.path.basename(filename))
    compressXml(filename, destTemplate)

  return 0


if __name__ == '__main__':
  sys.exit(main())
