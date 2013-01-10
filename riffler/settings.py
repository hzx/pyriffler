import os.path

# riffler
CURR_PATH = os.path.dirname(__file__)

TMP_PATH = '/tmp'

TEMPLATES_PATH = os.path.abspath(os.path.normpath(CURR_PATH + '/../templates'))

THIRD_PARTY_PATH = os.path.abspath(os.path.normpath(CURR_PATH + '/../third_party'))
JSON2 = os.path.join(THIRD_PARTY_PATH, 'json2.js')
HTMLCOMPRESSOR = os.path.join(THIRD_PARTY_PATH, 'htmlcompressor.jar')
CLOSURE_STYLESHEETS = os.path.join(THIRD_PARTY_PATH, 'closure-stylesheets.jar')
CLOSURE_COMPILER = os.path.join(THIRD_PARTY_PATH, 'compiler.jar')
