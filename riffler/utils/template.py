from tornado import template
from riffler import settings
from riffler.utils.file import readFile, writeFile
from riffler.utils.process import execute
from riffler.utils.image import encodeImage
import os.path, re


def compileTemplate(src, dest, params, files):
  # template parameters
  templateParams = {}

  # add params
  for name in params:
    templateParams[name] = params[name]

  # load files
  for name in files:
    templateParams[name] = readFile(files[name]).rstrip()

  # generate template
  destContent = template.Template(readFile(src), autoescape=None)\
      .generate(**templateParams)

  # save template
  writeFile(dest, destContent)


def compressHtml(src, dest):
  execute(
      'java', '-jar', settings.HTMLCOMPRESSOR, '--type', 'html',
      '--remove-intertag-spaces', '--remove-surrounding-spaces', 'all',
      '--output', dest, src)


def compressXml(src, dest):
  execute(
      'java', '-jar', settings.HTMLCOMPRESSOR, '--type', 'xml',
      '--output', dest, src)


def compressCss(src, mapFilename, dest):
  prepareCss(src)
  execute(
      'java', '-jar', settings.CLOSURE_STYLESHEETS,
      '--allow-unrecognized-properties',
      '--allow-unrecognized-functions',
      '--output-renaming-map-format', 'CLOSURE_UNCOMPILED',
      #'--output-renaming-map-format', 'CLOSURE_COMPILED',
      #'--output-renaming-map-format', 'JSON',
      #'--rename', 'CLOSURE',
      '--output-file', dest,
      '--output-renaming-map', mapFilename,
      src
      )
  optimized = processCss(dest)
  with open(dest, 'w') as f:
    f.write(optimized)


"""Prepare css for closure stylesheets

Add alternate comment if properties repeated
"""
def prepareCss(filename):
  alternateComment = '/* @alternate */ '
  repeats = []
  lines = []
  isSearchAlternate = False

  # create array of lines with alternate comment
  with open(filename, 'r') as f:
    for line in f:
      line = line.strip()
      # if block begin clear repeat list
      if line.find('{') >= 0:
        isSearchAlternate = True
        repeats = []
      if isSearchAlternate and len(line) > 0:
        # add all blocks to repeat list and search repeats
        colonIndex = line.find(':')
        if colonIndex >= 0:
          tag = line[0:colonIndex]
          tag = tag.strip()
          if tag in repeats:
            if line.find(alternateComment) == -1:
              line = alternateComment + line
          else:
            repeats.append(tag)
      if line.find('}') >= 0: isSearchAlternate = False
      lines.append(line)

  # save file
  with open(filename, 'w') as f:
    f.writelines(lines)


def processCss(filename):
  """ Reads and converts a css file by replacing all image references into
      base64 encoded images.
  """
  css = open(filename, 'r').read()
  cssDir = os.path.split(filename)[0]

  def transformUrl(match):
    imagefile = match.group(1)
    print("transformUrl, imagefile '%s'" % imagefile)
    # if the image is not local or can't be found, leave the url alone:
    if (imagefile.startswith('http://')
        or imagefile.startswith('https://')
        or not os.path.exists(os.path.join(cssDir, imagefile))):
      return match.group(0)
    return encodeImage(os.path.join(cssDir, imagefile))

  # pattern = 'url\((.*\.(svg|png|jpg|gif))\)'
  pattern = 'url\(([^)]+\.(svg|png|jpg|gif))\)'
  return re.sub(pattern, transformUrl, css)


def compressJs(src, cssMap, dest, jsMap):
  execute(
      'java', '-jar', settings.CLOSURE_COMPILER,
      # '--compilation_level', 'ADVANCED_OPTIMIZATIONS',
      '--compilation_level', 'SIMPLE_OPTIMIZATIONS',
      # '--warning_level', 'VERBOSE',
      '--process_jquery_primitives',
      #'--variable_map_input_file', jsMap,
      #'--variable_map_output_file',  jsMap,
      #'--js', '/home/dem/bin/closure-library/closure/goog/base.js', src,
      '--js', src,
      '--js_output_file', dest
      )

def getJsMapName(filename):
  name, ext = os.path.splitext(filename)
  return os.path.join(settings.TMP_PATH, '%s-js-map.js' % name)

def getCssMapName(filename):
  name, ext = os.path.splitext(filename)
  return os.path.join(settings.TMP_PATH, '%s-css-map.js' % name)

def compressCssJs(cssFilename, jsFilename):
  cssPath = os.path.join(settings.TMP_PATH, cssFilename)
  jsPath = os.path.join(settings.TMP_PATH, jsFilename)

  cssMap = getCssMapName(jsFilename)
  jsMap = getJsMapName(jsFilename)

  # create tmp js file
  jsTmp = jsPath + '.tmp'

  if os.path.exists(jsTmp): os.remove(jsTmp)

  prepareCss(cssPath)
  compressCss(cssPath, cssMap, cssPath)
  compressJs(jsPath, cssMap, jsTmp, jsMap)

  os.rename(jsTmp, jsPath)
