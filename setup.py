try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'ROM organizer with sickbeard-like web interface',
    'author': 'Leandro Penz',
    'url': 'https://github.com/lpenz/slickbird',
    'author_email': 'lpenz@lpenz.org',
    'version': '0.1',
    'install_requires': ['tornado'],
    'packages': ['slickbird'],
    'scripts': ['slickbird-start'],
    'name': 'slickbird'
}

setup(**config)
