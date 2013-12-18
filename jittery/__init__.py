
import os
import shutil
import sys

import jittery
from jittery.package import Package

def setup(**config):
  if len(sys.argv) > 1 and sys.argv[1] == 'build':
    dist = initialize_dist()
    packages = tuple(Package(name, dist) for name in config['packages'])
    for package in packages:
      package.compile()
    for package in packages:
      package.optimize()
  else:
    raise Exception('Currently the only accepted parameter is "build"')

def initialize_dist():
  js_dir = os.path.join(os.path.dirname(jittery.__file__), 'js/src')
  dist = 'dist'
  if os.path.isdir(dist):
    shutil.rmtree(dist)
  shutil.copytree(js_dir, dist)
  return dist
