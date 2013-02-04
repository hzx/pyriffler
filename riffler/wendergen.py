from mutant import coffeegen
from mutant import core
from mutant import common
from mutant import grammar


class WenderGen(object):
  """
  Convert mutant code tree to coffee code tree.
  """

  def __init__(self):
    self.domElementName = 'wender.DomElement'
    self.domTextName = 'wender.DomText'
    self.funcCounter = 0
    # cache generated modules
    self.cache = {}

  def genFuncName(self):
    self.funcCounter = self.funcCounter + 1
    return 'sys_renderItem%d' % self.funcCounter

  def createRenderItem(self, expr, parentClass):
    func = core.FunctionNode([common.Token(0, 'void', 'void')], self.genFuncName())

    # add param values
    func.addParameter('values', 'var')

    # add body
    ret = core.ReturnNode()
    ret.setBody(expr)
    func.addBodyNode(ret)

    # replace all values in expr with values[index].value
    valuesIndex = 0
    self.replaceParamVariables(expr, valuesIndex)
    
    return func

  def generate(self, module):
    self.genModule(module)

  def genModule(self, module):
    if self.cache.has_key(module.name):
      return
    self.cache[module.name] = ''

    self.module = module

    # convert structs to classes
    for name, st in module.structs.items():
      module.classes[name] = self.structToClass(st)

    # convert orm type creations with constructor
    # in global variables
    for name, va in module.variables.items():
      self.varToOrm(va)
    # in classes variables
    for name, cl in module.classes.items():
      for name, va in cl.variables.items():
        self.varToOrm(va)

    # search tag in function return nodes
    for name, func in module.functions.items():
      # search return node
      for bnode in func.bodyNodes:
        if (bnode.nodetype == 'return') and (bnode.body.nodetype == 'tag'):
          bnode.body = self.tagToElement(bnode.body, None)

    # search tags in methods
    for name, cl in module.classes.items():
      for fname, func in cl.functions.items():
        for bnode in func.bodyNodes:
          if (bnode.nodetype == 'return') and (bnode.body.nodetype == 'tag'):
            bnode.body = self.tagToElement(bnode.body, cl)

    # search crud in function values body, variables
    for name, func in module.functions.items():
      self.crudToOrm(func.bodyNodes)

    # search crud in class function values body
    for name, cl in module.classes.items():
      for fname, func in cl.functions.items():
        self.crudToOrm(func.bodyNodes)

    # generate imported modules
    for mn, mod in module.modules.items():
      self.genModule(mod)

  def structToClass(self, st):
    """
    Create class from struct st.
    """
    # choose baseName
    baseName = 'wender.OrmStruct'
    if 'id' in st.variables:
      baseName = 'wender.OrmHashStruct'

    # create class
    cl = core.ClassNode(st.name, baseName)

    # add constructor
    con = core.FunctionNode(None, None)
    superCall = core.FunctionCallNode('super')
    con.addBodyNode(superCall)

    superCall.addParameter(core.ValueNode("'%s'" % cl.name))
    if cl.name == 'World':
      cl.baseName = 'wender.World'
      superCall.addParameter(core.ValueNode("'world'"))
      superCall.addParameter(core.ValueNode('none'))
    else:
      # add params
      con.addParameter('name', 'var')
      con.addParameter('parent', 'var')
      # add super call to body
      superCall.addParameter(core.ValueNode('name'))
      superCall.addParameter(core.ValueNode('parent'))

    cl.setConstructor(con)

    # move variables
    for svname, sva in st.variables.items():
      # create variable
      va = core.VariableNode(sva.decltype, sva.name)

      # create variable init body
      body = None
      defaultValue = None

      if self.isArrayType(sva):
        body = core.FunctionCallNode('wender.OrmList')
        # add params
        typeParam = core.ValueNode("'%s'" % sva.decltype[0].word)

      elif self.isStructType(sva):
        # take word from single token in declaration type
        bodyClass = sva.decltype[0].word
        body = core.FunctionCallNode(bodyClass)
        # add params
        typeParam = core.ValueNode("'%s'" % bodyClass)

      else:
        body = core.FunctionCallNode('wender.OrmValue')
        # add params
        typeParam = core.ValueNode("'%s'" % sva.decltype[0].word)
        # add default value
        if 'default' in sva.inits:
          defaultValue = sva.inits['default']

      nameParam = core.ValueNode("'%s'" % sva.name)
      thisParam = core.ValueNode('this')

      body.isConstructorCall = True
      body.addParameter(typeParam)
      body.addParameter(nameParam)
      body.addParameter(thisParam)
      if defaultValue != None:
        body.addParameter(defaultValue)
      va.setBody(body)

      # add to class
      cl.addVariable(va)

    return cl

  def crudToOrm(self, nodes):
    """
    Convert structs to orm classes, crud operations to orm crud methods
    """
    # search struct constructor call
    for node in nodes:
      if node.nodetype == 'variable':
        self.varToOrm(node)

  def varToOrm(self, va):
    """
    Convert array of struct to wender.OrmList
    """
    # for array create initialization with OrmList
    if self.isArrayOfStructType(va):
      # create OrmList
      ol = core.FunctionCallNode('wender.OrmList')
      ol.isConstructorCall = True
      # add params
      vatype = common.getOnlyName(va.decltype[0].word)
      # type
      ol.addParameter(core.ValueNode("'%s'" % vatype))
      # name
      ol.addParameter(core.ValueNode('none'))
      # parent
      ol.addParameter(core.ValueNode('none'))
      va.body = ol

  def tagToElement(self, tag, parentClass):
    """
    Convert TagNode to FunctionCallNode.
    parentClass None if tag in global function
    """
    element = core.FunctionCallNode(self.domElementName)
    element.isConstructorCall = True

    # add tagName
    tagValue = core.ValueNode("'%s'" % tag.name)
    tagValue.isLitString = True
    element.addParameter(tagValue)

    attrs = core.DictBodyNode()
    # add attributes
    for attrName, attrBody in tag.attributes.items():
      attrs.addItem(attrName, attrBody)
    element.addParameter(attrs)

    childs = []
    paramList = None
    paramRender = None

    # if one child and name rmap - create reactive map: add list and render list item
    if len(tag.childs) == 1:
      child = tag.childs[0]
      # we have reactive map
      if (child.nodetype == 'functioncall'):
        if child.name == 'rmap':
          if len(child.params) != 2:
            raise Exception('rmap must have 2 params, module "%s"' % self.module.name)
          paramList = child.params[0]
          paramRender = child.params[1]
        elif child.name == 'rvalue':
          if len(child.params) != 2:
            raise Exception('rvalue must have 2 params, module "%s"' % self.module.name)
          val = child.params[0]
          valRender = child.params[1]
          renderElem = core.FunctionCallNode(valRender.value)
          renderElem.addParameter(core.ValueNode(val.value))
          # add renderElem to childs
          childs.append(renderElem)

    # add childs
    if paramList == None and len(childs) == 0:
      for child in tag.childs:
        if child.nodetype == 'functioncall':
          childs.append(self.functioncallToText(child, parentClass))
          continue
        if child.nodetype == 'value':
          childs.append(self.valueToText(child, parentClass))
          continue
        if child.nodetype == 'tag':
          childs.append(self.tagToElement(child, parentClass))
          continue
        raise Exception('unknown tag child nodetype, current "%s", module "%s"' % (child.nodetype, self.module.name))

    # element.addParameter(childs)
    childArr = core.ArrayBodyNode()
    for child in childs:
      childArr.addItem(child)
    element.addParameter(childArr)
    
    if paramList == None:
      # add list
      element.addParameter(core.ValueNode('none'))
      # add list item render
      element.addParameter(core.ValueNode('none'))
    else:
      # add list
      element.addParameter(paramList)
      # add list item render
      element.addParameter(paramRender)

    return element

  def valueToText(self, value, parentClass):
    """
    Create and return 
    """
    domtext = core.FunctionCallNode(self.domTextName)
    domtext.isConstructorCall = True
    if value.isName:
      nameValue = core.ValueNode("''")
      nameValue.isLitString = True

      # create values array node
      valuesArr = core.ArrayBodyNode()
      valuesArr.addItem(value)

      # create render function node
      renderFunc = core.FunctionNode([common.Token(0, 'void', 'void')], self.genFuncName())
      renderFunc.addParameter('values', 'var')
      ret = core.ReturnNode()
      ret.setBody(core.ValueNode('values[0].value'))
      renderFunc.addBodyNode(ret)

      domtext.addParameter(nameValue)
      domtext.addParameter(valuesArr)

      if parentClass:
        parentClass.addFunction(renderFunc)
        renderValue = core.ValueNode('this.' + renderFunc.name)
      else:
        self.module.functions[renderFunc.name] = renderFunc
        renderValue = core.ValueNode(renderFunc.name)

      renderValue.isName = True
      domtext.addParameter(renderValue)
    else:
      nameValue = core.ValueNode(value.value)
      nameValue.isName = True
      domtext.addParameter(nameValue)
      domtext.addParameter(core.ValueNode('none'))
      domtext.addParameter(core.ValueNode('none'))
    return domtext

  def functioncallToText(self, fcall, parentClass):
    # create render function
    domtext = core.FunctionCallNode(self.domTextName)
    domtext.isConstructorCall = True
    # search variable values
    values = self.searchParamVariables(fcall)
    # create render item function
    renderFunc = self.createRenderItem(fcall, parentClass)

    # add params to text func

    # text
    # text.addParameter(common.Token(0, "''", grammar.LITSTRING_TYPE))
    domtext.addParameter(core.ValueNode("''"))
    # values
    domtext.addParameter(values)
    # renderValues
    if parentClass:
      parentClass.addFunction(renderFunc)
      domtext.addParameter(core.ValueNode('this.' + renderFunc.name))
    else:
      self.module.functions[renderFunc.name] = renderFunc
      domtext.addParameter(core.ValueNode(renderFunc.name))
    # domtext.addParameter(renderFunc)

    return domtext

  def searchParamVariables(self, fcall):
    values = []
    for node in fcall.params:
      if node.nodetype == 'value':
        # have name
        if node.isName:
          # create value node
          values.append(node)
          continue
        else:
          continue
        raise Exception('searchParamVariables unkdown param.body.wordtype "%s"' % node.body.wordtype)
      if node.nodetype == 'functioncall':
        values = values + self.searchParamVariables(node)
        continue
      raise Exception('searchParamVariables function call params contain unkdown nodetype "%s"' % node.nodetype)

    arr = core.ArrayBodyNode()
    for val in values:
      arr.addItem(val)

    return arr

  def replaceParamVariables(self, fcall, index):
    params = []

    for node in fcall.params:
      # replace variable value by array value node
      if (node.nodetype == 'value') and not (node.value.isdigit() or node.value[0] == ";"):
        # arrVal = core.ArrayValueNode(common.Token(0, 'values', 'name'), index)
        val = core.ValueNode('values[%d].value' % index)
        index = index + 1
        params.append(val)
      else:
        # for function replace param recursive
        if (node.nodetype == 'functioncall'):
          index = self.replaceParamVariables(node, index)
        params.append(node)

    fcall.params = params

    return index

  def isArrayType(self, va):
    return (len(va.decltype) == 3) and (va.decltype[1].word == '[') and (va.decltype[2].word == ']')

  def isStructType(self, va):
    return (len(va.decltype) == 1) and common.isStructName(self.module, va.decltype[0].word)

  def isArrayOfStructType(self, va):
    return self.isArrayType(va) and common.isStructName(self.module, va.decltype[0].word)

