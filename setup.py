import sys

from setuptools import setup
from setuptools import find_packages

version = '0.0.0'

# Please update tox.ini when modifying dependency version requirements
install_requires = [
    'pycrypto>=2.6',
    'setuptools>=1.0',
    'six',
    'cmd2>=0.6.9',
    'sarge>=0.1.4',
    'psutil',
    'pid>=2.0.1',
    'blessed>=1.14.1',
    'future',
    'coloredlogs',
    'humanfriendly>=2.1'
]

# env markers in extras_require cause problems with older pip: #517
# Keep in sync with conditional_requirements.py.
if sys.version_info < (2, 7):
    install_requires.extend([
        # only some distros recognize stdlib argparse as already satisfying
        'argparse',
        'mock<1.1.0',
    ])
else:
    install_requires.append('mock')


dev_extras = [
    'nose',
    'pep8',
    'tox',
]

docs_extras = [
    'Sphinx>=1.0',  # autodoc_member_order = 'bysource', autodoc_default_flags
    'sphinx_rtd_theme',
    'sphinxcontrib-programoutput',
]


setup(
    name='chat-roulette-server',
    version=version,
    description='Chat Roulette',
    url='https://deadcode.me',
    author="ph4r05@deadcode.me",
    author_email='ph4r05@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
    ],

    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev': dev_extras,
        'docs': docs_extras,
    },
)
