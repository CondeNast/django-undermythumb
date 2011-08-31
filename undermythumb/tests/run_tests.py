#!/usr/bin/env python

import os
import sys


os.environ['DJANGO_SETTINGS_MODULE'] = 'undermythumb.tests.test_settings'

parent = os.path.realpath(os.path.join(os.path.dirname(__file__), 
                                       os.path.pardir, 
                                       os.path.pardir))
sys.path.insert(0, parent)

from django.conf import settings
from django.test.simple import run_tests


def runtests():
    failures = run_tests(['tests'], verbosity=1, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
