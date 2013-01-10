import base64
import uuid
import os.path
from riffler import settings

def generateCookieSecret():
  return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

def generateUniqueFilename():
  return str(uuid.uuid4())

def generateTmpFilename():
  return os.path.join(settings.TMP_PATH, generateUniqueFilename())
