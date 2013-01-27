try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'jittery_python is a python -> javascript transpiler.',
    'author': 'Paul Harper',
    'url': 'https://github.com/benekastah/jittery-python',
    'download_url': 'https://github.com/benekastah/jittery-python/archive/master.zip',
    'author_email': 'benekastah@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['jittery_python'],
    'scripts': ["bin/jittery"],
    'name': 'jittery_python'
}

setup(**config)
