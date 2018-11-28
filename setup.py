#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os

from setuptools import setup, find_packages

version = __import__('kingfisher').__version__
here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

reqs = [line.strip() for line in open('requirements.txt')]

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Natural Language :: English',
    "Programming Language :: Python :: 2",
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Topic :: Scientific/Engineering :: Atmospheric Science',
    'License :: OSI Approved :: Apache Software License',
]

setup(name='kingfisher',
      version=version,
      description="A Web Processing Service for Earth-Observation Data Analysis",
      long_description=README + '\n\n' + CHANGES,
      author="Nils Hempelmann",
      author_email='info@nilshempelmann.de',
      url='https://github.com/bird-house/kingfisher',
      classifiers=classifiers,
      license="Apache Software License 2.0",
      keywords='wps pywps birdhouse kingfisher',
      packages=find_packages(),
      include_package_data=True,
      install_requires=reqs,
      entry_points={
          'console_scripts': [
             'kingfisher=kingfisher.cli:cli',
          ]},)
