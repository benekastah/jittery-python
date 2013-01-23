import os

try:
    if os.environ['JITTERY_PYTHON']:
        from jittery_python import setup
except KeyError:
    try:
        from setuptools import setup
    except ImportError:
        from distutils.core import setup

config = {
    'description': 'My Project',
    'author': 'My Name',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'My email.',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['jittery_python'],
    'scripts': ["bin/jittery"],
    'name': 'projectname'
}

setup(**config)
