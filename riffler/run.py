#!/usr/bin/env python

import os
import os.path
import sys


TOOLS_PATH = os.path.abspath(os.path.dirname(__file__))


sys.path.insert(0, TOOLS_PATH)
from rbtls import settings


sys.path.insert(0, settings.SERVER_PATH)
from rb.site.main import mainMulti


if __name__ == '__main__':
  sys.exit(mainMulti())
