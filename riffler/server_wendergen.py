from mutant import core
from mutant import common
from mutant import grammar
import re


class ServerWenderGen(object):
  """
  Create world model in app.
  Convert tag to text,
  expression in tags to str(expressions).
  all world right values to self.world
  """

  def __init__(self):
    self.cache = {}

    self.handlerImport = 'from wender import handlers as whandlers'
    self.handlerBasename = 'whandlers.BaseHandler'

    self.nodetypeToGen = {
        'value': self.genValue,
        'variable': self.genVariable,
        'if': self.genIf,
        'for': self.genFor,
        'array_body': self.genArrayBody,
        'array_value': self.genArrayValue,
        'dict_body': self.genDictBody,
        'return': self.genReturn,
        'functioncall': self.genFunctionCall,
        'insert': self.genInsert,
        'select_count': self.genSelectCount,
        'select_one': self.genSelectOne,
        'select_from': self.genSelectFrom,
        'select_concat': self.genSelectConcat,
        'select_sum': self.genSelectSum,
        'update': self.genUpdate,
        'delete_from': self.genDeleteFrom,
        'tag': self.genTag,
      }

  def generate(self, access, module):
    self.mainModule = module
    self.genModule(access, module)

  def genModule(self, access, module):
    if module.name in self.cache: return
    self.cache[module.name] = ''

    self.module = module
    self.access = access
    self.addAuthImport = False

    # process classes
    self.processClasses(module)

    # process functions
    self.processFunctions(module)

    # process variables
    self.processVariables(module)

    self.processStructs(module)

    self.createHandlers(module)

    if self.addAuthImport:
      module.rawimports.append('from tornado.web import authenticated')

    # process imported modules
    for name, mod in module.modules.items():
      if mod: self.genModule(access, mod)

  def createHandlers(self, module):
    # search urls in variables
    if not ('urls' in module.variables): return
    urls = module.variables['urls']
    if not (urls.nodetype == 'variable' and urls.body and urls.body.nodetype == 'array_body'):
      self.sayError('urls must be variable and body must be array_body')

    # to module add import wender.handlers
    module.rawimports.append(self.handlerImport)

    # new body with handler class
    urlbody = core.ArrayBodyNode()

    # for every handler create handler class
    for item in urls.body.items:
      url, func, name = item.items
      # get module function
      fn = self.module.functions[func.value]
      # create handler class
      handler = self.createHandlerClass(fn)
      module.addClass(handler)
      # add new item
      newitem = core.ArrayBodyNode()
      newitem.addItem(url)
      newitem.addItem(core.ValueNode(handler.name))
      urlbody.addItem(newitem)

      # delete handler function
      del self.module.functions[func.value]

    urls.body = urlbody

  def createHandlerClass(self, fn):
    # create class
    name = fn.name[0].upper() + fn.name[1:len(fn.name)]
    handler = core.ClassNode(name, self.handlerBasename)

    # add get method
    getfunc = core.FunctionNode([common.Token(0, 'void', 'void')], 'get')
    handler.addFunction(getfunc)

    # fill body with fn body
    getfunc.bodyNodes = fn.bodyNodes

    # if access is admin add attribute restriction
    if self.access == 'admin':
      getfunc.attributes = getfunc.attributes + '@authenticated\n'
      self.addAuthImport = True
  
    return handler

  # processors

  def processClasses(self, module):
    pass

  def processFunctions(self, module):
    for fname, fn in module.functions.items():
      module.functions[fname] = self.genFunction(fn)

  def processVariables(self, module):
    pass

  def processStructs(self, module):
    pass

  # generators

  def genFunction(self, fn, cl=None):
    nodes = []
    for node in fn.bodyNodes:
      gen = self.nodetypeToGen[node.nodetype]
      nodes.append(gen(node))
    fn.bodyNodes = nodes
    return fn

  def genValue(self, va, cl=None):
    return va

  def genVariable(self, va, cl=None):
    pass

  def genIf(self, ifn, cl=None):
    pass

  def genFor(self, forn, cl=None):
    pass

  def genArrayBody(self, ab, cl=None):
    pass

  def genArrayValue(self, av, cl=None):
    pass

  def genDictBody(self, db, cl=None):
    pass

  def genReturn(self, ret, cl=None):
    body = self.genByNodetype(ret.body, cl)
    ret.body = body
    return ret

  def genFunctionCall(self, fc, cl=None):
    return fc

  def genInsert(self, va, cl=None):
    pass

  def genSelectCount(self, va, cl=None):
    pass

  def genSelectOne(self, va, cl=None):
    pass

  def genSelectFrom(self, va, cl=None):
    pass

  def genSelectConcat(self, va, cl=None):
    pass

  def genSelectSum(self, va, cl=None):
    pass

  def genUpdate(self, upd, cl=None):
    pass

  def genDeleteFrom(self, df, cl=None):
    pass

  def genTag(self, tag, cl=None):
    nodes = self.genTagTag(tag)
    # compile nodes
    return core.ValueNode('')

  def genTagTag(self, tag):

    attrs = []
    for attr in tag.attributes.items():
      pass

    childs = []
    for child in tag.childs:
      pass

    valName = core.ValueNode('<%s ' % tag.name)
    valName.isTagString = True
    valNameEnd = core.ValueNode('>')
    valNameEnd.isTagString = True
    valNameClose = core.ValueNode('</%s>' % tag.name)
    valNameClose.isTagString = True

    nodes = [valName, attrs, valNameEnd, childs, valNameClose]

    return nodes

  def genTagString(self, tag, cl=None):
    childs = []
    for child in tag.childs:
      if child.nodetype == 'tag':
        childs.append(self.genTagString(child, cl))
      # elif child.nodetype == 'value':
      #   childs.append(self.genValue)
      # elif child.nodetype == 'functioncall':
      #   childs.append(self.genFunctionCall)
    attrs = []
    for name, attr in tag.attributes.items():
      attrs.append('%s=""' % name)
    return '<%s %s>%s</%s>' % (tag.name, ' '.join(attrs), ''.join(childs), tag.name)

  def genByNodetype(self, node, cl=None):
    gen = self.nodetypeToGen[node.nodetype]
    return gen(node, cl)

  def sayError(self, msg):
    raise Exception('ServerWenderGen: %s, module "%s"' % (msg, self.module.name))

  def flushUrls(self, urls):
    pass
