#!/usr/bin/env python

import os
import sys


os.environ['DJANGO_SETTINGS_MODULE'] = 'undermythumb.tests.test_settings'

parent = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                       os.path.pardir,
                                       os.path.pardir))
sys.path.insert(0, parent)

from django.test.simple import DjangoTestSuiteRunner


def runtests():
    runner = DjangoTestSuiteRunner(verbosity=1, interactive=True)
    failures = runner.run_tests(['tests'])
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
