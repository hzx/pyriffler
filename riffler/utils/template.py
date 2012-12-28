from tornado import template
from rbtls import settings
from rbtls.utils.file import readFile, writeFile
from rbtls.utils.process import execute
from rbtls.utils.image import encodeImage
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
  destContent = template.Template(readFile(src))\
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
  execute(
      'java', '-jar', settings.CLOSURE_STYLESHEETS,
      '--allow-unrecognized-properties',
      '--allow-unrecognized-functions',
      '--output-renaming-map-format', 'CLOSURE_UNCOMPILED',
      #'--output-renaming-map-format', 'CLOSURE_COMPILED',
      #'--output-renaming-map-format', 'JSON',
      '--rename', 'CLOSURE',
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
    # if the image is not local or can't be found, leave the url alone:
    if (imagefile.startswith('http://')
        or imagefile.startswith('https://')
        or not os.path.exists(os.path.join(cssDir, imagefile))):
      return match.group(0)
    return encodeImage(cssDir, imagefile)

  pattern = 'url\((.*\.(svg|png|jpg|gif))\)'
  return re.sub(pattern, transformUrl, css)


def compressJs(src, cssMap, dest, jsMap):
  print(src)
  execute(
      'java', '-jar', settings.CLOSURE_COMPILER,
      '--compilation_level', 'ADVANCED_OPTIMIZATIONS',
      '--warning_level', 'VERBOSE',
      '--process_jquery_primitives',
      #'--variable_map_input_file', jsMap,
      #'--variable_map_output_file',  jsMap,
      #'--js', '/home/dem/bin/closure-library/closure/goog/base.js', src,
      '--js', src,
      '--js_output_file', dest
      )
