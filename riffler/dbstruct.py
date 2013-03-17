import pymongo
from pymongo.mongo_client import MongoClient
from mutant import grammar

class Field(object):
  kind = 'field'

  def __init__(self, name, params):
    self.name = name
    self.params = params

class IndexField(object):
  kind = 'index'

  def __init__(self, name, params, direction):
    self.name = name
    self.params = params
    self.direction = direction

class StructField(object):
  kind = 'struct'

  def __init__(self, name, params):
    self.name = name
    self.params = params
    self.fields = []

class DbStruct(object):

  def __init__(self, structs):
    self.structs = structs

    self.indexDirectionMap = {
        'asc': pymongo.ASCENDING,
        'desc': pymongo.DESCENDING,
      }

  def createIndexes(self, dbname):
    pass

  def parseWorld(self):
    """
    return
    [
      struct_field,
      struct_field,
      struct_field,
    ]
    """
    fields = self.parseStruct('World')

  def parseStruct(name):
    fields = self.getStructFields(name)
    return [self.parseField(fname, params) for fname, params in fields.items()]

  def parseField(self, name, params):
    """
    return field
    """
    paramtype = params['type']

    if paramtype in grammar.VALUE_TYPES:
      if 'index' in params:
        field = IndexField(name, params, self.getIndexDirection(params))
      else:
        field = Field(name, params)
    else:
      field = StructField(name, params)
      # not parse params for ref and link
      if not(('ref' in params) or ('link' in params)):
        # parse struct field params
        field.fields = self.parseStruct(paramtype)

    return field

  def parseIndexes(self, fields):
    """
    [
      [doc_name, field_dot_name, index_direction],
      [doc_name, field_dot_name, index_direction],
      [doc_name, field_dot_name, index_direction],
    ]
    """
    indexes = []
    for field in fields:
      docName = [field.name]
      fieldNames = []

  def searchIndexFields(self, fields, out):
    for field in fields:
      # skip simple values
      if field.kind == 'field':
        continue
      # add index field
      if field.kind == 'index':
        out.append(field.name)
        continue
      # search index fields
      if field.kind == 'struct':
        pass

  def parseIndex(self, field):
    pass

  def getStructFields(self, name):
    fields = self.structs.get(name, None)
    if not fields:
      raise Exception('dbstruct.getStruct: struct with name "%s" not found' % name)
    return fields

  def getIndexDirection(self, params):
    direction = params['index']
    dbdirection = self.indexDirectionMap.get(direction, None)
    if not dbdirection:
      raise Exception('index direction unknown "%s"' % direction)
    return dbdirection
