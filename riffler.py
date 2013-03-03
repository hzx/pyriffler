#!/usr/bin/env python
import sys
import os
import os.path

RIFFLER_FILE = os.path.realpath(__file__)
RIFFLER_PATH = os.path.dirname(RIFFLER_FILE)
CURRENT_PATH = os.path.abspath('.')
PROJECT_FILE = os.path.join(CURRENT_PATH, 'project')

# now not needed, python insert it automatic for current script
# sys.path.insert(0, RIFFLER_PATH)
from riffler import settings
sys.path.insert(0, settings.MUTANT_PATH)

from riffler.wender_builder import WenderBuilder


HELP = """
usage:
  riffler debug
  make debug build

  riffler release
  make release build

  riffler create appname
  create application structure for new appname project
"""

def usage():
  print HELP

def checkProjectExists():
  if not os.path.exists(PROJECT_FILE):
    print 'not found project file "%s"' % PROJECT_FILE
    sys.exit(1)

def taskDebug():
  taskBuild(isDebug=True)

def taskRelease():
  taskBuild(isDebug=False)

def taskBuild(isDebug):
  checkProjectExists()

  builder = WenderBuilder()
  builder.build(PROJECT_FILE, isDebug)

def taskCreate():
  # check param count
  if len(sys.argv) <= 2:
    usage()
    return

  appName = sys.argv[2]
  print 'task create NOT IMPLEMENTED, appName "%s"' % appName

def taskDb():
  print 'task db NOT IMPLEMENTED'

def main():
  taskMap = {
      'debug': taskDebug,
      'release': taskRelease,
      'create': taskCreate,
      'db': taskDb,
    }

  # by default use task debug
  if len(sys.argv) == 1:
    taskDebug()
  else:
    # search task
    taskName = sys.argv[1]
    if taskName in taskMap:
      task = taskMap[taskName]
      task()
    # for errors show usage
    else:
      usage()

  return 0

if __name__ == '__main__':
  sys.exit(main())

