import subprocess
import sys


def execute(*command):
  exitcode = subprocess.call(command)
  if exitcode != 0:
    sys.exit(exitcode)


# TODO(dem) check CalledProcessError and make sys.exit with code
def executeWithOutput(*command):
  output = subprocess.check_output(command)
  return output
    
