#!/usr/bin/env python

import os
from setuptools import setup


def get_readme():
    md_path = os.path.join(os.path.dirname(__file__), "README.md")
    txt_path = os.path.join(os.path.dirname(__file__), "README.txt")

    if os.path.exists(txt_path):
        d = open(txt_path).read()
    elif os.path.exists(md_path):
        d = open(md_path).read()
    else:
        d = ""
    return d


setup(name='pyplr',
      version='0.1',
      author='Joel T. Martin',
      author_email='joel.t.martin36@gmail.com',
      description='Software for researching the pupillary light reflex',
      license='BSD',
      keywords='eyetracking pupillometry melanopsin instrumentation',
      url='https://github.com/jtmbeta/pyplr',
      install_requires=['scipy', 'numexpr', 'tables', 'pandas'],
      packages=['pyplr'],
      long_description=get_readme(),
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Science/Research',
      ],
      )
