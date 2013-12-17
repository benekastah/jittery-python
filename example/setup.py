from jittery import setup

config = {
    'description': 'Example jittery app',
    'author': 'Paul Harper',
    'url': 'https://github.com/benekastah/jittery-python',
    'download_url': 'https://github.com/benekastah/jittery-python/archive/master.zip',
    'author_email': 'benekastah@gmail.com',
    'version': '0.1',
    'packages': ['jittery_app'],
    'name': 'jittery_app'
}

setup(**config)
