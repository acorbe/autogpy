#!/usr/bin/env python

from distutils.core import setup

setup(name='autogpy',
      description = "autogpy: AutoGnuplot.py - automatic generation of gnuplot figures (including script and data) from python",
      version='0.1',
      author='Alessandro Corbetta',
      author_email='a.corbetta@tue.nl',
      url='https://github.com/acorbe/autogpy',
      packages=['autogpy'],
      license="new BSD",
      install_requires = ['numpy>=1.8']
)
