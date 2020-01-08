#!/usr/bin/env python

from distutils.core import setup

dependencies = ["boto3"]
test_dependencies = []

setup(name='dynamo-db-time-series',
      version='0.0.6',
      description='Tool to play with dynamo db and time series',
      author='Adrian Galera',
      author_email='adrian.galera.87@gmail.com',
      url='',
      install_requires=dependencies
      , extras_require={"test": test_dependencies}
      )
