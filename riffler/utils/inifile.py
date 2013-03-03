import re


class IniReader(object):

  def __init__(self):
    self.categoryRe = re.compile('^\s*\[([^]]+)\]\s*$')
    self.propertyRe = re.compile('^\s*([a-zA-Z_0-9]+)\s*=\s*([\S]*)\s*$')
    self.categories = []
    self.currentProperties = None

  def read(self, filename):
    """
    Read filename ini.
    Return array
    [
      [ 'category', { name: value } ]
    ]
    """

    # read file lines
    with open(filename, 'r') as f: lines = f.read().splitlines()

    for line in lines:
      if not self.parseCategory(line):
        self.parseProperty(line)

    return self.categories

  def parseCategory(self, line):
    res = self.categoryRe.findall(line)
    if len(res) == 0: return False

    # create category
    category = [ res[0], {} ]
    
    # add to categories
    self.categories.append(category)
    self.currentProperties = category[1]

    return True

  def parseProperty(self, line):
    res = self.propertyRe.findall(line)
    if len(res) == 0: return False

    if self.currentProperties == None:
      raise Exception('Found property without category')

    self.currentProperties[res[0][0]] = res[0][1]

    return True
