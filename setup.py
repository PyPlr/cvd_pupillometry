#!/usr/bin/env python

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyplr', # Replace with your own username
    version='0.0.6',
    author='Joel T. Martin',
    author_email='joel.t.martin36@gmail.com',
    description='Software for researching the pupillary light reflex',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/PyPlr/cvd_pupillometry',
    project_urls={'Documentation': 'https://pyplr.github.io/cvd_pupillometry/', 
        'bioRxiv preprint':'https://www.biorxiv.org/content/10.1101/2021.06.02.446731v1'},
    install_requires=['scipy','matplotlib','msgpack','pyzmq','requests','numpy','seaborn','seabreeze','numexpr','tables','pandas'],
    packages=setuptools.find_packages(),
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Science/Research',
          'Programming Language :: Python :: 3.7'
      ],
      )
