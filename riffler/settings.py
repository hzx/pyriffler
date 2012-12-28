import os.path


# src/tools/rb/settings.py
SRC_PATH = os.path.abspath(os.path.normpath(os.path.dirname(__file__) +  '/../..'))

CLIENT_PATH = os.path.join(SRC_PATH, 'client')

SERVER_PATH = os.path.join(SRC_PATH, 'server')

# src/server/templates
TEMPLATE_PATH = os.path.join(SRC_PATH, 'server/templates')
SRC_TEMPLATE_PATH = os.path.join(SRC_PATH, 'server/src_templates')

# src/server/static
STATIC_PATH = os.path.join(SRC_PATH, 'server/static')

# src/server/static/js
JS_PATH = os.path.join(STATIC_PATH, 'js')

# src/style
STYLE_PATH = os.path.join(SRC_PATH, 'style')

# src/server/static/css
CSS_PATH = os.path.join(STATIC_PATH, 'css')

# rubear/src/../third_party
THIRD_PARTY_PATH = os.path.join(os.path.dirname(SRC_PATH), 'third_party')
HTMLCOMPRESSOR = os.path.join(THIRD_PARTY_PATH, 'htmlcompressor.jar')
CLOSURE_STYLESHEETS = os.path.join(THIRD_PARTY_PATH, 'closure-stylesheets.jar')
CLOSURE_COMPILER = os.path.join(THIRD_PARTY_PATH, 'compiler.jar')
