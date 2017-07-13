"""Functional tests that verify that we can talk to Autograph.
"""

import base64
import os.path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile
import pytest
from tests import get_test_file, ADDON_FILENAME
from aws_lambda import sign_xpi


@pytest.yield_fixture
def temp_directory():
    tempdir = tempfile.mkdtemp()
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def test_sign_xpi_generates_signed_xpi(temp_directory):
    unsigned_addon = os.path.join(temp_directory, ADDON_FILENAME)
    shutil.copy(get_test_file(ADDON_FILENAME), unsigned_addon)
    guid = 'hypothetical-addon@mozilla.org'
    env = {
        'autograph_server_url': 'http://localhost:8000',
        "autograph_hawk_id": "alice",
        "autograph_hawk_secret": ("fs5wgcer9qj819kfptdlp8gm227"
                                  "ewxnzvsuj9ztycsx08hfhzu"),
        "autograph_key_id": "extensions-ecdsa"
    }
    unsigned_file = open(unsigned_addon, 'rb')
    new_xpi = sign_xpi.sign_xpi(env, unsigned_file, guid)
    new_xpi_as_zip = ZipFile(new_xpi)

    def extract_single(filename):
        extracted_filename = os.path.join(temp_directory, filename)
        archive_filename = os.path.join('META-INF', filename)
        open(extracted_filename, 'wb').write(
            new_xpi_as_zip.read(archive_filename))

    extract_single('manifest.mf')
    extract_single('mozilla.rsa')
    extract_single('mozilla.sf')
    manifest_mf = os.path.join(temp_directory, 'manifest.mf')
    mozilla_sf = os.path.join(temp_directory, 'mozilla.sf')
    mozilla_rsa = os.path.join(temp_directory, 'mozilla.rsa')

    openssl = subprocess.Popen([
        "openssl", "smime", "-verify", "-in",
        mozilla_rsa,
        '-inform', 'DER', '-content',
        mozilla_sf,
        '-noverify'
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    (stdout, stderr) = openssl.communicate()
    assert not openssl.returncode

    openssl_sha1 = subprocess.Popen([
        "openssl", "dgst", "-sha1", "-binary",
        manifest_mf,
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    # Verify that we calculated the sha1 correctly
    (sha1_raw, stderr) = openssl_sha1.communicate()
    assert not openssl_sha1.returncode
    sha1 = base64.b64encode(sha1_raw)

    sigmanifest_lines = open(mozilla_sf).readlines()
    sha1_lines = [
        line for line in sigmanifest_lines
        if line.startswith('SHA1-Digest-Manifest')
    ]
    assert len(sha1_lines) == 1
    sha1_line = sha1_lines[0]
    (_, our_sha1) = sha1_line.split()

    assert our_sha1 == sha1.decode('utf-8')
