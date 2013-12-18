
import os
import re
import subprocess

import jittery
from jittery.compiler import Compiler

re_slash = re.compile(r'/')
re_ext = re.compile(r'\.py$')

class Package():
  def __init__(self, name, out_dir, working_dir=None):
    self.name = name
    if working_dir:
      self.source_path = os.path.join(working_dir, self.name)
    else:
      self.source_path = self.name
    self.main_out_dir = out_dir
    self.out_dir = os.path.join(self.main_out_dir, self.name)

  def get_module_name(self, fname):
    module_name = re.sub(re_slash, '.', fname)
    module_name = re.sub(re_ext, '', module_name)
    if module_name == '%s.__main__' % self.name:
      module_name = '__main__'
    return module_name

  def compile(self):
    os.makedirs(self.out_dir, exist_ok=True)
    for dirname, dirnames, filenames in os.walk(self.source_path):
      for fname in filenames:
        if re.search(re_ext, fname):
          full_fname = os.path.join(dirname, fname)
          self.compile_file(fname, full_fname)

  def compile_file(self, fname, full_fname):
    module_name = self.get_module_name(full_fname)
    f = open(full_fname)
    source = f.read()
    f.close()
    compiler = Compiler(source, module_name, package=self)
    js = compiler.compile()
    outfile = os.path.join(self.out_dir, '%s.js' % fname)
    of = open(outfile, 'w+')
    of.write(js)

  def optimize(self):
    closurebuilder = os.path.join(
      self.main_out_dir,
      'closure-library/closure/bin/build/closurebuilder.py')
    roots = []
    for dirname in os.listdir(self.main_out_dir):
      dirname = os.path.join(self.main_out_dir, dirname)
      if os.path.isdir(dirname):
        roots.append('--root=%s' % dirname)
    namespace = '--namespace=%s.__main__' % self.name
    output_mode = '--output_mode=compiled'
    compiler = '--compiler_jar=%s' % os.path.join(
      os.path.dirname(jittery.__file__),
      '../bin/closure_compiler/compiler.jar')
    output_file = '--output_file=%s/%s.js' % (self.main_out_dir, self.name)
    compiler_flags = list(map(lambda f: '--compiler_flags=%s' % f, [
      '--compilation_level=ADVANCED_OPTIMIZATIONS',
      # '--closure_entry_point=%s.__entry_point__' % self.name,
      # '--process_closure_primitives',
    ]))
    subprocess.call([
      'python', closurebuilder, namespace, output_mode, compiler, output_file
    ] + roots + compiler_flags)
