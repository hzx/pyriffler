from mutant import core
from mutant import common
from mutant import grammar
import re


class WenderGen(object):
  """
  Convert mutant code tree to coffee code tree.
  """

  def __init__(self):
    self.domRawElementName = 'wender.DomRawElement'
    self.domElementName = 'wender.DomElement'
    self.domTextName = 'wender.DomText'
    self.funcCounter = 0
    # cache generated modules
    self.cache = {}
    self.eventname_re = re.compile('^on([a-zA-Z_]+)$')
    self.dot_re = re.compile('\.')

  def genFuncName(self):
    self.funcCounter = self.funcCounter + 1
    return 'sys_method%d' % self.funcCounter

  def createRenderItem(self, expr, parentClass):
    func = core.FunctionNode([common.Token(0, 'void', 'void')], self.genFuncName())

    # add param values
    func.addParameter('values', [common.Token(0, 'robject', 'robject'), common.Token(0, '[', '['), common.Token(0, ']', ']')])

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

    self.processTags(module)

    self.processVariables(module)

    self.processOrm(module)

    self.processStructs(module)

    # generate imported modules
    for mn, mod in module.modules.items():
      self.genModule(mod)

  def processStructs(self, module):
    # convert structs to classes
    for name, st in module.structs.items():
      module.classes[name] = self.structToClass(st)


  # search tag node and convert to element
  def processTags(self, module):
    # search in variables
    for name, va in module.variables.items():
      if va.body and va.body.nodetype == 'tag':
        va.body = self.tagToElement(va.body, None)

    # search in functions
    for name, func in module.functions.items():
      self.searchTag(func.bodyNodes, None)


    for name, cl in module.classes.items():
      # search in class variables
      for vname, va in cl.variables.items():
        if va.body and va.body.nodetype == 'tag':
          va.body = self.tagToElement(va.body, cl)
      # search in class functions
      for fname, func in cl.functions.items():
        self.searchTag(func.bodyNodes, cl)

  def searchTag(self, nodes, cl):
    for node in nodes:
      if node.nodetype == 'variable' and node.body and node.body.nodetype == 'tag':
        node.body = self.tagToElement(node.body, cl)
      elif node.nodetype == 'value' and node.body and node.body.nodetype == 'tag':
        node.body = self.tagToElement(node.body, cl)
      elif node.nodetype == 'return' and node.body.nodetype == 'tag':
        node.body = self.tagToElement(node.body, cl)
      elif node.nodetype == 'if':
        self.searchTag(node.body, cl)
        self.searchTag(node.elseBody, cl)

  def processVariables(self, module):
    """
    Search variables and lists,
    convert to ObservableValue, ObservableList
    """
    for vname, var in module.variables.items():
      # search right values in variables

      # search left values in variables - this must be error
      pass

    for fname, func in module.functions.items():
      # search right values in functions
      func.bodyNodes = self.genObservables(func.bodyNodes, func, None)

      # search left values in functions

    for cname, cl in module.classes.items():
      for vname, var in cl.variables.items():
        # search right values in class variables

        # search left values in class variables - this must be error
        pass

      for fname, func in cl.functions.items():
        # search right values in class functions
        # self.processStructFieldInFunction(func, cl)
        func.bodyNodes = self.genObservables(func.bodyNodes, func, cl)

        # search left values in class functions

  def processOrm(self, module):
    # convert orm type creations with constructor
    # in global variables
    for name, va in module.variables.items():
      self.varToOrm(va)
    # in classes variables
    for name, cl in module.classes.items():
      for name, va in cl.variables.items():
        self.varToOrm(va)

    # search orm values
    # in global functions
    for name, func in module.functions.items():
      self.ormValueToValueInFunction(func)
    # in classes functions
    for name, cl in module.classes.items():
      for fname, func in cl.functions.items():
        self.ormValueToValueInFunction(func)

    # search crud in function values body, variables
    for name, func in module.functions.items():
      self.crudToOrm(func.bodyNodes)

    # search crud in class function values body
    for name, cl in module.classes.items():
      for fname, func in cl.functions.items():
        self.crudToOrm(func.bodyNodes)

  def structToClass(self, st):
    """
    Create class from struct st.
    For value and for list constructor have type, name, parent
    For struct constructor have name, parent
    """
    # choose baseName
    baseName = 'wender.OrmStruct'
    if 'id' in st.variables:
      baseName = 'wender.OrmHashStruct'

    # create class
    cl = core.ClassNode(st.name, baseName)

    # add constructor
    con = core.FunctionNode(None, None)
    cl.setConstructor(con)
    # add super call to constructor
    superCall = core.FunctionCallNode('super')
    con.addBodyNode(superCall)

    # add super call parameters
    superCall.addParameter(core.ValueNode("'%s'" % cl.name))
    if cl.name == 'World':
      cl.baseName = 'wender.World'
      superCall.addParameter(core.ValueNode("'world'"))
      superCall.addParameter(core.ValueNode('none'))
    else:
      # add params
      con.addParameter('name', [common.Token(0, 'string', 'string')])
      con.addParameter('parent', [common.Token(0, 'object', 'name')])
      # add super call to vainit
      superCall.addParameter(core.ValueNode('name'))
      superCall.addParameter(core.ValueNode('parent'))

    # move variables from struct to class
    for svname, sva in st.variables.items():
      # create variable
      va = core.VariableNode(sva.decltype, sva.name)

      # create variable init body
      vainit = None
      typeParam = None
      defaultValue = None

      if self.isArrayType(sva):
        vainit = core.FunctionCallNode('wender.OrmList')
        # add params
        typeParam = core.ValueNode("'%s'" % sva.decltype[0].word)

      elif self.isStructType(sva):
        # take word from single token in declaration type
        vaclass = sva.decltype[0].word
        vainit = core.FunctionCallNode(vaclass)
        # add params - for struct type not needed
        # typeParam = core.ValueNode("'%s'" % vaclass)

      else:
        vainit = core.FunctionCallNode('wender.OrmValue')
        # add params
        typeParam = core.ValueNode("'%s'" % sva.decltype[0].word)
        # add default value
        if 'default' in sva.inits:
          defaultValue = sva.inits['default']

      nameParam = core.ValueNode("'%s'" % sva.name)
      thisParam = core.ValueNode('this')

      vainit.isConstructorCall = True
      if typeParam: vainit.addParameter(typeParam)
      vainit.addParameter(nameParam)
      vainit.addParameter(thisParam)
      if defaultValue != None:
        vainit.addParameter(defaultValue)
      va.setBody(vainit)

      # print 'class "%s", wendergen.structToClass type "%s", name "%s", this "%s"' % (cl.name, va.body.params[0].value, va.body.params[1].value, va.body.params[2].value)

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
    convert event variable to wender.ObservableEvent
    """
    # for array create initialization with OrmList
    # if self.isArrayOfStructType(va) and va.body and va.body.nodetype != 'functioncall':
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
    # convert event variable to wender.ObservableEvent and initialize
    elif self.isEventType(va):
      evinit = core.FunctionCallNode('wender.ObservableEvent')
      evinit.isConstructorCall = True
      va.setBody(evinit)

  def ormValueToValueInFunction(self, func):
    """
    Search orm value in function body
    """
    pass

  def ormNodeToValue(self, node):
    """
    Add to ValueNode.name suffix .value if name is OrmValue object.
    """
    # test value body contains orm value
    if (node.nodetype == 'value') and (node.isName):
      # check if name is ormvalue
      pass

  def tagToElement(self, tag, parentClass):
    """
    Convert TagNode to FunctionCallNode.
    parentClass None if tag in global function
    """
    if tag.name == 'raw':
      return self.createDomRawElementObject(tag)
    return self.createDomElementObject(tag, parentClass) if tag.name in grammar.HTML_TAGS else self.createViewFactory(tag, parentClass)

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
      renderFunc.addParameter('values', [common.Token(0, 'robject', 'robject'), common.Token(0, '[', '['), common.Token(0, ']', ']')])
      ret = core.ReturnNode()
      ret.setBody(core.ArrayValueNode('values', 0))
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

  def createRawText(self, node):
    domtext = core.FunctionCallNode(self.domTextName)
    domtext.isConstructorCall = True
    domtext.addParameter(node)
    domtext.addParameter(core.ValueNode('none'))
    domtext.addParameter(core.ValueNode('none'))

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
        val = core.ArrayValueNode('values', index)
        index = index + 1
        params.append(val)
      else:
        # for function replace param recursive
        if (node.nodetype == 'functioncall'):
          index = self.replaceParamVariables(node, index)
        params.append(node)

    fcall.params = params

    return index

  def genObservables(self, nodes, func, cl):
    converted = []
    for node in nodes:
      processed = self.processObservableNode(node, func, cl)
      converted.append(processed)

    return converted

  def processObservableNode(self, node, func, cl):
    if node.nodetype == 'variable':
      node.body = self.processObservableNode(node.body, func, cl)
    elif node.nodetype == 'value':
      # not process world value
      # if node.value == 'world':
      #   return node
      if self.isObservableValueName(node.value, func, cl):
        if node.body and node.bodyReactive:
        # if node.body:
          # debug
          # print 'value "%s", bodyReactive "%s"' % (node.value, str(node.bodyReactive))

          setvalue = core.FunctionCallNode('%s.setValue' % node.value)

          param = self.processObservableNode(node.body, func, cl)
          setvalue.addParameter(param)

          # value = core.ValueNode('%s.value' % node.value)
          # value.body = self.processObservableNode(node.body, func, cl)
          return setvalue
        else:
          value = core.ValueNode('%s.value' % node.value)
          return value
    elif node.nodetype == 'if':
      node.body = self.genObservables(node.body, func, cl)
      node.elseBody = self.genObservables(node.elseBody, func, cl)
    elif node.nodetype == 'for':
      pass
    elif node.nodetype == 'array_value':
      if self.isObservableListName(node.value, func, cl):
        value = core.ValueNode('%s[%s].value' % (node.value, node.index))
        return value
    elif node.nodetype == 'functioncall':
      # process params
      params = []
      for param in node.params:
        processed = self.processObservableNode(param, func, cl)
        params.append(processed)
      node.params = params
    elif node.nodetype == 'return':
      node.body = self.processObservableNode(node.body, func, cl)
    return node

  # def processStructFieldInFunction(self, func, cl):
  #   for node in func.bodyNodes:

  def createDomRawElementObject(self, tag):
    attrs = core.DictBodyNode()
    childs = core.ArrayBodyNode()
    # add attributes
    for attrName, attrBody in tag.attributes.items():
      attrs.addItem(attrName, attrBody)

    # create element
    element = core.FunctionCallNode(self.domRawElementName)
    element.isConstructorCall = True
    element.addParameter(tag.childs[0])
    element.addParameter(attrs)
    element.addParameter(childs)
    element.addParameter(core.ValueNode('none'))
    element.addParameter(core.ValueNode('none'))

    return element

  # TODO(dem) move here from method
  def createDomElementObject(self, tag, parentClass):
    attrs = core.DictBodyNode()
    childs = core.ArrayBodyNode()
    paramList = None
    paramRender = None

    # add attributes
    for attrName, attrBody in tag.attributes.items():
      attrs.addItem(attrName, attrBody)

    # add list and render
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
          childs.addItem(renderElem)
        elif child.name == 'rraw':
          if len(child.params) != 1:
            raise Exception('rraw must have 1 params, module "%s"' % self.module.name)
          childs.addItem(self.createRawText(child.params[0]))
        elif child.name == 'rfunction':
          # create function call node and add to childs
          if len(child.params) != 1:
            raise Exception('rfunction must have 1 param, module "%s"' % self.module.name)
          renderFunc = core.FunctionCallNode(child.params[0].value)
          childs.addItem(renderFunc)

    # add childs
    if paramList == None and len(childs.items) == 0:
      for child in tag.childs:
        if child.nodetype == 'functioncall':
          childs.addItem(self.functioncallToText(child, parentClass))
          continue
        if child.nodetype == 'value':
          childs.addItem(self.valueToText(child, parentClass))
          continue
        if child.nodetype == 'tag':
          childs.addItem(self.tagToElement(child, parentClass))
          continue
        raise Exception('unknown tag child nodetype, current "%s", module "%s"' % (child.nodetype, self.module.name))

    # create element
    element = core.FunctionCallNode(self.domElementName)
    element.isConstructorCall = True
    # add all params
    nameParam = core.ValueNode("'%s'" % tag.name)
    nameParam.isLitString = True
    element.addParameter(nameParam)
    element.addParameter(attrs)
    element.addParameter(childs)
    element.addParameter(paramList if paramList else core.ValueNode('none'))
    element.addParameter(paramRender if paramRender else core.ValueNode('none'))

    return element

  def createViewFactory(self, tag, parentClass):
    # create factory method
    decltype = [common.Token(0, tag.name, 'name')]
    factory = core.FunctionNode(decltype, self.genFuncName())

    # add factory method
    if parentClass:
      parentClass.addFunction(factory)
    else:
      self.moduleFunctions[factory.name] = factory

    # add view creation
    view = core.VariableNode([common.Token(0, tag.name, 'name')], 'view')
    createView = core.FunctionCallNode(tag.name)
    createView.isConstructorCall = True
    view.setBody(createView)
    factory.addBodyNode(view)

    # add view attrs assignment
    for name, attr in tag.attributes.items():
      result = self.eventname_re.findall(name)
      # add event
      if len(result):
        evassign = core.FunctionCallNode('view.addEvent')
        evassign.addParameter(core.ValueNode('view.event' + result[0]))
        evassign.addParameter(attr)
        factory.addBodyNode(evassign)
      # add member assign
      else:
        memassign = core.ValueNode('view.' + name)
        memassign.isName = True
        memassign.setBody(attr)
        factory.addBodyNode(memassign)

    # add view.element render
    elrender = core.ValueNode('view.element')
    elrender.isName = True
    elrender.setBody(core.FunctionCallNode('view.render'))
    factory.addBodyNode(elrender)

    # add return view
    ret = core.ReturnNode()
    retBody = core.ValueNode('view')
    retBody.isName = True
    ret.setBody(retBody)
    factory.addBodyNode(ret)

    return core.FunctionCallNode('this.' + factory.name if parentClass else factory.name)

  def isEventType(self, va):
    return (len(va.decltype) == 1) and (va.decltype[0].word == 'event')

  def isArrayType(self, va):
    return (len(va.decltype) == 3) and (va.decltype[1].word == '[') and (va.decltype[2].word == ']')

  def isStructType(self, va):
    return (len(va.decltype) == 1) and common.isStructName(self.module, va.decltype[0].word)

  def isArrayOfStructType(self, va):
    return self.isArrayType(va) and common.isStructName(self.module, va.decltype[0].word)

  def isStructValue(self, name, func, cl):
    """
    Search variable declaration,
    check variable is simple type of struct, or robject type.
    """
    # name must be struct parent type and simple type
    isStructParent = False
    isSimpleType = False
    # split name
    parts = self.dot_re.split(name)
    partsCount = len(parts)


    # if partsCount == 1
    # search in func params or in global variables

    # if partsCount >= 2 then
    # if parts[0] == 'this' then search in class variables
    # then if parts[0] is module name then search in module variables by parts
    # then search in func params by parts
    # then search in variables by parts


    if parts[0] == 'this' and len(parts) >= 2:
      # search variable in class variables
      decltype = self.searchVarTypeInClassVariables(parts[1], cl)

      if decltype:
        print 'isStructFieldSimple name "%s" decltype "%s"' % (name, decltype[0].word)
    else:
      for part in parts:
        # search variable in func params
        decltype = self.searchVarTypeInFunctionParams(part, func) if func else None
        # search variable in variables
        decltype = decltype if decltype else self.searchVarTypeInVariables(part, self.module)
        if decltype:
          print 'isStructFieldSimple name "%s" decltype "%s"' % (part, decltype[0].word)
    return isStructParent and isSimpleType

  def searchVarTypeInVariables(self, name, module):
    va = module.variables.get(name, None)
    return va.decltype if va else None

  def searchVarTypeInFunctionParams(self, name, func):
    for paramName, paramType in func.params:
      if paramName == name: return paramType
    return None

  def searchVarTypeInClassVariables(self, name, cl):
    va = cl.variables.get(name, None)
    return va.decltype if va else None

  def isObservableValueName(self, name, func, cl):
    """
    Search name type, must be struct simple field or robject
    struct, robject
    """
    # raise Exception('implement isStructFieldSimple')
    # split name
    parts = self.dot_re.split(name)
    count = len(parts)
    firstName = parts[0]

    if count == 1:
      return False

    # if name begin from this then search in class variables
    if firstName == 'this' and cl:
      vname = parts[1]
      va = cl.variables.get(vname, None)
      # is function name
      if va == None: return False
        # raise Exception('module "%s", class "%s" not contain "%s" variable, class variables "%s"' % (self.module.name, cl.name, vname, cl.getVariablesName()))
      if self.isStructType(va) or va.decltype[0].word == 'robject':
        return True
    # is value from world
    elif firstName == 'world':
      # TODO(dem) remove this hack
      if len(parts) == 1:
        return False
      return True
    else:
      # check if value from func params
      if func:
        for pname, pdecltype in func.params:
          if firstName == pname:
            firstType = pdecltype[0].word
            if firstType == 'robject' or common.isStructName(self.module, firstType):
              return True
    # if value from robject list
    # if value from struct
    return False

  def isObservableListName(self, name, func, cl):
    """
    list of struct, robject
    """
    parts = self.dot_re.split(name)
    firstName = parts[0]
    # if begin from this then search in class variables
    if firstName == 'this' and cl:
      vname = parts[1]
      va = cl.variables[vname]
      if self.isArrayType(va) == False:
        return False
      firstType = va.decltype[0].word
      if firstType == 'robject' or common.isStructName(firstType):
        return True
    elif firstName == 'world':
      # TODO(dem) check struct field is array type
      return True
    else:
      if func:
        for pname, pdecltype in func.params:
          if firstName == pname:
            firstType = pdecltype[0].word
            if firstType == 'robject' or common.isStructName(self.module, firstType):
              return True
    return False
