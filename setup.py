#!/usr/bin/env python

from setuptools import setup

with open("README.md", "r") as fh:
        long_description = fh.read()

setup(name='autogpy',
      description = "autogpy: AutoGnuplot.py - automatic generation of gnuplot figures (including script and data) from python",
      version='0.1.1',
      author='Alessandro Corbetta',
      author_email='a.corbetta@tue.nl',
      url='https://github.com/acorbe/autogpy',
      long_description = long_description,
      long_description_content_type="text/markdown",
      packages=['autogpy'],
      license="new BSD",
      install_requires = ['numpy>=1.8']
)
