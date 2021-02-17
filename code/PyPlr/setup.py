#!/usr/bin/env python

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyplr-jtmbeta', # Replace with your own username
    version='0.0.1',
    author='Joel T. Martin',
    author_email='joel.t.martin36@gmail.com',
    description='Software for researching the pupillary light reflex',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jtmbeta/PyPlr',
    install_requires=['scipy','matplotlib','msgpack','pyzmq','requests','numpy','seaborn','seabreeze','spectres','numexpr','tables','pandas'],
    packages=setuptools.find_packages(),
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Science/Research',
      ],
      )
