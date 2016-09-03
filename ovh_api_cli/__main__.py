#!/usr/bin/env python
# -*- coding=utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import sys

# If we are running from a wheel, add the wheel to sys.path
if __package__ == '':
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)

import ovh_api_cli

if __name__ == '__main__':
    sys.exit(ovh_api_cli.main())
