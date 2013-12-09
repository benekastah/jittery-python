try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'jittery is a python -> javascript transpiler.',
    'author': 'Paul Harper',
    'url': 'https://github.com/benekastah/jittery-python',
    'download_url': 'https://github.com/benekastah/jittery-python/archive/master.zip',
    'author_email': 'benekastah@gmail.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['jittery'],
    'scripts': ["bin/"],
    'name': 'jittery'
}

setup(**config)
