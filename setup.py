import os

from setuptools import setup, find_packages


# XXX: these should go into the package's __init__
VERSION = '0.1.0'
AUTHOR = 'FND'
LICENSE = 'BSD'

DESC = open(os.path.join(os.path.dirname(__file__), 'README')).read()

META = {
    'name': 'tiddlywebplugins.tagdex',
    'url': 'https://github.com/FND/tiddlywebplugins.tagdex',
    'version': VERSION,
    'description': 'TiddlyWeb indexer for tag-based tiddler retrieval',
    'long_description': DESC,
    'license': LICENSE,
    'author': AUTHOR,
    'packages': find_packages(exclude=['test']),
    'platforms': 'Posix; MacOS X; Windows',
    'include_package_data': False,
    'zip_safe': False,
    'install_requires': ['tiddlyweb', 'tiddlywebplugins.utils'],
    'extras_require': {
        'testing': ['pytest', 'wsgi-intercept', 'httplib2'],
        'coverage': ['figleaf', 'coverage']
    }
}


if __name__ == '__main__':
    setup(**META)
