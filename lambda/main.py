"""
sign-xpi: Sign an XPI file
"""

import os.path
import sys
DIR = os.path.dirname(os.path.abspath(__file__))
SITE_PACKAGES = os.path.join(DIR, "site-packages")
sys.path.insert(0, SITE_PACKAGES)

from sign_xpi import handle  # noqa: E402
__all__ = ['handle']
