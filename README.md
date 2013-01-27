jittery-python
==============

A python to javascript transpiler. It is written in python, making use of CPython's `ast` module to do all the parsing. The compilation is then performed on the generated ast and a roughly equivalent bit of javascript is spat out for each node. Currently, the semantics are more javascript than python. Over time, there will be a range of options that allow you to code closer to javascript or python, depending on your preferences and what performance characteristics you require (javascript style will generally be faster than code generated to run exactly like python).

More documentation will come later describing excatly which structures work properly and which do not. Many core library functions are not implemented, so currently this is only useful for experimentation and curiosity. This has only been tested on CPython 3.3, and is not guaranteed to work on any other python at this time. Furthermore, since jittery-python is alpha software, it is also not guaranteed to work on CPython 3.3.

# Setup

Once you clone this repo, you can run the setup script:

```bash
$ cd jittery_python
$ python setup.py install
```

You should then have access to the `jittery` command. You don't need to run the setup script, though; you can just access the `jittery` command from `bin/jittery`. Running `jittery --help` should give you some ideas on how you can use it. Here are a few basic examples:

## Compile files

You can import your own files using relative paths. This currently doesn't work quite the way python does it. In time I'll have it recognize and compile packages by providing my own `setup` function for `setup.py`. It will always compile a single result file, no matter how many python files were used.

```bash
# This will create the file __main__.py.js
$ jittery -c path/to/__main__.py
# You can also specify an outfile
$ jittery -c path/to/__main__.py -o main.js
```

## Test code in realtime

I don't have a repl going at the moment, but I have something closeish:

```bash
# This will take the python code you input, compile it to javascript, use node to run it and print the result.
# The result is the last line you input.
$ jittery -eps "
class Greeter:
  def __init__(self, name):
    self.name = name

  def greet(self, guest_name):
    print('I, ' + self.name + ', hereby greet thee, ' + guest_name + '.')

g = Greeter('Jameson III')
g.greet('benekastah')

x = 5**2
"
```

This particular command should output:

```bash
Warning: == and != are not yet properly implemented. Currently an `is` or `is not` operation is used instead.
I Jameson III hereby greet thee, Paul
25
```

You can also view the generated javascript by removing the `-e` option:

```bash
$ jittery -ps "...code"
```
