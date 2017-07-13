"""Unit test package for sign_xpi package."""

import os.path

TEST_DIR, _ = os.path.split(__file__)
ADDON_FILENAME = 'hypothetical-addon-unsigned.xpi'


def get_test_file(filename):
    return os.path.join(TEST_DIR, filename)
