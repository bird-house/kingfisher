# -*- coding: utf-8 -*-

"""
This module is used to manage optional dependencies.

Example usage::

    from birdy.dependencies import ipywidgets as widgets
"""

import warnings
from .exceptions import SnappyWarning

warnings.filterwarnings('default', category=SnappyWarning)

try:
    from snappy import ProductIO
    from snappy import jpy
except ImportError:
    ProductIO = None
    jpy = None
    warnings.warn('ESA snap is not supported. Please install *snappy*.', SnappyWarning)
