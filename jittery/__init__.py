
import os
import re
import shutil
import sys
import subprocess

import jittery
from jittery.compiler import Compiler

def setup(**config):
  if len(sys.argv) > 1 and sys.argv[1] == 'build':
    packages = config['packages']
    initialize_dist()
    for package in packages:
      compile_package(package)
    for package in packages:
      optimize_package(package)
  else:
    raise Exception('Currently the only accepted parameter is "build"')

re_slash = re.compile(r'/')
re_ext = re.compile(r'\.py$')

def get_module_name(fname, package):
  module_name = re.sub(re_slash, '.', fname)
  module_name = re.sub(re_ext, '', module_name)
  if module_name == '%s.__main__' % package:
    module_name = '__main__'
  return module_name

def compile_package(package):
  dist_path = os.path.join('dist', package)
  os.makedirs(dist_path, exist_ok=True)
  for dirname, dirnames, filenames in os.walk(package):
    for fname in filenames:
      if re.search(re_ext, fname):
        full_fname = os.path.join(dirname, fname)
        compile_package_file(fname, full_fname, dist_path, package)

def compile_package_file(fname, full_fname, dist_path, package):
  module_name = get_module_name(full_fname, package)
  f = open(full_fname)
  source = f.read()
  f.close()
  compiler = Compiler(source, module_name, package=package)
  js = compiler.compile()
  outfile = os.path.join(dist_path, '%s.js' % fname)
  of = open(outfile, 'w+')
  of.write(js)

def initialize_dist():
  js_dir = os.path.join(os.path.dirname(jittery.__file__), 'js/src')
  dist = 'dist'
  if os.path.isdir(dist):
    shutil.rmtree(dist)
  shutil.copytree(js_dir, dist)

def optimize_package(package):
  closurebuilder = 'dist/google_closure/closure/bin/build/closurebuilder.py'
  roots = []
  dist = 'dist'
  for dirname in os.listdir(dist):
    dirname = os.path.join(dist, dirname)
    if os.path.isdir(dirname):
      roots.append('--root=%s' % dirname)
  namespace = '--namespace=%s.__main__' % package
  output_mode = '--output_mode=compiled'
  compiler = '--compiler_jar=dist/google_closure/compiler/compiler.jar'
  output_file = '--output_file=dist/%s.js' % package
  compiler_flags = list(map(lambda f: '--compiler_flags=%s' % f, [
    '--compilation_level=ADVANCED_OPTIMIZATIONS',
    # '--closure_entry_point=%s.__entry_point__' % package,
    # '--process_closure_primitives',
  ]))
  subprocess.call([
    'python', closurebuilder, namespace, output_mode, compiler, output_file
  ] + roots + compiler_flags)
