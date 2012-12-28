import base64
import uuid

def generateCookieSecret():
  return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)
