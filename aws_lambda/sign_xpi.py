import base64
import hashlib
import logging
import os.path
import email.utils
import sys
import tempfile
import zipfile

import boto3
import json
import marshmallow.fields
import rdflib
import requests
from requests_hawk import HawkAuth
from sign_xpi_lib import XPIFile
from six.moves.urllib.parse import urljoin, unquote

CHUNK_SIZE = 512 * 1024

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')


class SignXPIError(Exception):
    """Abstract base class for errors in this lambda."""


class ChecksumMatchError(SignXPIError):
    def __init__(self, url, expected_checksum, actual_checksum):
        message = "When fetching {}, expected checksum {} (got {})".format(
            url, expected_checksum, actual_checksum)
        super(ChecksumMatchError, self).__init__(message)
        self.url = url
        self.expected_checksum = expected_checksum
        self.actual_checksum = actual_checksum


class S3IdNotPresentError(SignXPIError):
    def __init__(self, s3_key):
        message = "S3 path was not prefixed with an XPI ID (got {})".format(
            s3_key)
        super(S3IdNotPresentError, self).__init__(message)
        self.s3_key = s3_key


class S3IdMatchError(SignXPIError):
    def __init__(self, xpi_id, s3_id):
        message = "XPI ID was {} (S3 path starts with {})".format(
            xpi_id, s3_id)
        super(S3IdMatchError, self).__init__(message)
        self.xpi_id = xpi_id
        self.s3_id = s3_id


class Environment(marshmallow.Schema):
    autograph_hawk_id = marshmallow.fields.String(
        required=True, load_from="AUTOGRAPH_HAWK_ID")
    autograph_hawk_secret = marshmallow.fields.String(
        required=True, load_from="AUTOGRAPH_HAWK_SECRET")
    autograph_server_url = marshmallow.fields.String(
        required=True, load_from="AUTOGRAPH_SERVER_URL")
    autograph_key_id = marshmallow.fields.String(
        required=True, load_from="AUTOGRAPH_KEY_ID")
    output_bucket = marshmallow.fields.String(
        required=True, load_from="OUTPUT_BUCKET")


class SourceInfo(marshmallow.Schema):
    """
    Describes the location of the XPI, as either a URL or an S3 location.

    Requires either URL, or bucket + key.
    """
    url = marshmallow.fields.URL()
    bucket = marshmallow.fields.String()
    key = marshmallow.fields.String()

    @marshmallow.decorators.validates_schema
    def verify_either_url_or_s3_info(self, data):
        if data.get('url'):
            return

        if data.get('bucket') and data.get('key'):
            return

        raise marshmallow.exceptions.ValidationError(
            "Either a URL or an S3 location (bucket + key) must be provided",
            ["url", "bucket", "key"])


class BucketData(marshmallow.Schema):
    name = marshmallow.fields.String(required=True)


class ObjectData(marshmallow.Schema):
    key = marshmallow.fields.String(required=True)

    @marshmallow.pre_load
    def unencode_key(self, in_data):
        """De-URL-encode keys

        S3 events appear to have URL-encoded keys for reasons that
        aren't clear. Perhaps all keys need to be URL-encoded on the
        wire and boto handles it transparently for us? Whatever the
        reasoning, undo it.

        """
        key = in_data['key']
        return {**in_data, "key": unquote(key)}


class S3Data(marshmallow.Schema):
    bucket = marshmallow.fields.Nested(BucketData, required=True)
    object = marshmallow.fields.Nested(ObjectData, required=True)


class EventRecord(marshmallow.Schema):
    s3 = marshmallow.fields.Nested(S3Data, required=True)


class S3Event(marshmallow.Schema):
    records = marshmallow.fields.List(
        marshmallow.fields.Nested(EventRecord),
        load_from='Records',
        required=True)


class SignEvent(marshmallow.Schema):
    source = marshmallow.fields.Nested(SourceInfo, required=True)
    checksum = marshmallow.fields.String()


def handle(event, context, env=os.environ):
    """
    Handle a sign-xpi event.
    """

    event = S3Event(strict=True).load(event).data
    env = Environment(strict=True).load(env).data

    ret = []

    for record in event['records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info("Retrieving from S3 bucket=%s key=%s",
                    bucket, key)
        (localfile, filename) = retrieve_xpi(record)
        logger.info("Retrieved S3 bucket=%s key=%s => localfile=%s",
                    bucket, key, localfile.name)
        guid = get_guid(localfile)
        logger.info("Retrieved extension ID for localfile=%s => guid=%s",
                    localfile.name, guid)
        verify_extension_id(record, guid)
        logger.info("Signing localfile=%s guid=%s", localfile.name, guid)
        signed_xpi = sign_xpi(env, localfile, guid)
        logger.info("Uploading signed XPI as filename=%s guid=%s",
                    filename, guid)
        ret.append(upload(env, open(signed_xpi, 'rb'), filename))

    return ret


def upload(env, signed_xpi, filename):
    bucket = s3.Bucket(env['output_bucket'])
    bucket.put_object(Body=signed_xpi, Key=filename)

    return {
        "uploaded": {
            "bucket": bucket.name,
            "key": filename,
        }
    }


def retrieve_xpi(event):
    """Download the XPI to some local file, verifying its checksum is correct.

    Returns a local "temporary" file containing the XPI as well as its
    "filename" as best as we could deduce.

    :return: (localfile, filename)

    """
    localfile = tempfile.NamedTemporaryFile()
    s3_data = event['s3']
    key = s3_data['object']['key']
    obj = s3.Object(s3_data['bucket']['name'], key)
    obj.download_fileobj(localfile)
    filename = key
    if '/' in filename:
        (_, filename) = key.rsplit('/', 1)

    return localfile, filename


def extract_response_filename(response):
    """Extract the content-disposition filename, or None if we can't."""
    content_disposition = response.headers.get('Content-Disposition')
    if not content_disposition:
        return None

    parameters = content_disposition.split(';')
    if parameters[0].strip() != 'attachment':
        return None

    for parameter in parameters[1:]:
        name, value = parameter.strip().split('=', 1)
        if name == 'filename':
            return email.utils.unquote(value)

    return None


def compute_checksum(contents):
    # Always use sha256 for now
    h = hashlib.sha256()
    h.update(contents.read())
    return h.hexdigest()


def get_guid(xpi_file):
    ext_id = get_extension_id(zipfile.ZipFile(xpi_file))
    if len(ext_id) <= 64:
        return ext_id
    return hashlib.sha256(ext_id).hexdigest()


def verify_extension_id(event, xpi_id):
    key = event['s3']['object']['key']
    if '/' not in key:
        raise S3IdNotPresentError(key)
    (event_id, _) = key.split('/')
    if event_id != xpi_id:
        raise S3IdMatchError(xpi_id, event_id)


def get_extension_id(zipfile):
    contents = zipfile.namelist()
    if 'install.rdf' in contents:
        return get_extension_id_rdf(zipfile.open('install.rdf'))
    elif 'manifest.json' in contents:
        return get_extension_id_json(zipfile.open('manifest.json'))

    raise ValueError("Extension is missing a manifest")


def get_extension_id_json(manifest_json):
    # Note: doesn't go to any lengths to support comments, unlike AMO
    # (see for example
    # https://github.com/mozilla/addons-server/blob/f554850626c2940d66f71b8f72ce86544e58bbd3/src/olympia/files/utils.py#L283)
    manifest = json.load(manifest_json)
    applications = manifest.get('applications', {})
    gecko = applications.get('gecko', {})
    ext_id = gecko.get('id', None)
    if not ext_id:
        raise ValueError("Extension does not have ID in manifest.json")
    return ext_id


INSTALL_RDF_MANIFEST = rdflib.term.URIRef(u'urn:mozilla:install-manifest')
INSTALL_RDF_NAMESPACE = 'http://www.mozilla.org/2004/em-rdf'
INSTALL_RDF_ID_PREDICATE = rdflib.term.URIRef(
    '{}#{}'.format(INSTALL_RDF_NAMESPACE, "id"))


def get_extension_id_rdf(install_rdf):
    # This is based off of code in AMO's utils.py. See:
    # https://github.com/mozilla/addons-server/blob/f554850626c2940d66f71b8f72ce86544e58bbd3/src/olympia/files/utils.py
    graph = rdflib.Graph()
    graph.load(install_rdf)
    if list(graph.triples((INSTALL_RDF_MANIFEST, None, None))):
        root = INSTALL_RDF_MANIFEST
    else:
        root = graph.subjects(None, INSTALL_RDF_MANIFEST).next()

    id_object = next(graph.objects(root, INSTALL_RDF_ID_PREDICATE))
    # This is an rdflib.term.Literal, which is a subclass of Unicode
    return str(id_object)


def sign_xpi(env, localfile, guid):
    """
    Use the Autograph service to sign the XPI.

    :returns: filename of the signed XPI
    """
    xpi_file = XPIFile(localfile)
    auth = HawkAuth(id=env['autograph_hawk_id'],
                    key=env['autograph_hawk_secret'])
    b64_payload = base64.b64encode(xpi_file.signature.encode('utf-8'))
    url = urljoin(env['autograph_server_url'], '/sign/data')
    key_id = env['autograph_key_id']
    resp = requests.post(url, auth=auth, json=[{
        "input": b64_payload.decode('utf-8'),
        "keyid": key_id,
        "options": {
            "id": guid,
        }
    }])
    resp.raise_for_status()
    signature = base64.b64decode(resp.json()[0]['signature'])

    # FIXME: make_signed doesn't support NamedTemporaryFile or
    # anything like that; we have to provide an actual filename.
    # Try to generate a sensible filename.
    # FIXME: I guess the caller has to remember to delete this file.
    # Hopefully there's no other calls to a similarly-named file??
    (localstem, localext) = os.path.splitext(localfile.name)
    output_file = localstem + '-signed' + localext

    xpi_file.make_signed(output_file, sigpath="mozilla.rsa",
                         signed_manifest=xpi_file.signature,
                         signature=signature)
    return output_file


if __name__ == '__main__':
    env = {
        "AUTOGRAPH_SERVER_URL": "http://localhost:8000/",
        "AUTOGRAPH_HAWK_ID": "alice",
        "AUTOGRAPH_HAWK_SECRET": ("fs5wgcer9qj819kfptdlp8gm227"
                                  "ewxnzvsuj9ztycsx08hfhzu"),
        "AUTOGRAPH_KEY_ID": "extensions-ecdsa",
        "OUTPUT_BUCKET": "eglassercamp-addon-sign-xpi-output",
    }
    print(handle(json.loads(sys.stdin.read()), None, env))
