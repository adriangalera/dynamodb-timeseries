#!/usr/bin/env python

from distutils.core import setup

dependencies = ["boto3"]

setup(name='kinesistsconsumer',
      version='0.0.1',
      description='App that reads a kinesis timeseries stream and consolidates the items to DynamoDB',
      author='Adrian Galera',
      author_email='adrian.galera.87@gmail.com',
      url='',
      install_requires=dependencies
      # , extras_require={"test": test_dependencies}
      )
