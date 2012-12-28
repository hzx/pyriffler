


def readFile(filename):
  with open(filename, 'r') as f: return f.read()


def writeFile(filename, content):
  with open(filename, 'w') as f: f.write(content)


def cat(sources, dest):
  with open(dest, 'w') as writer:
    for filename in sources:
      with open(filename, 'r') as reader: writer.write(reader.read()) 
