"""
The CLI command for the sign-xpi lambda.
"""

import argparse
import boto3
import hashlib
import json
import os.path
import sys
import traceback

DEFAULT_S3_BUCKET = 'eglassercamp-addon-sign-xpi-input'

s3 = boto3.resource('s3')
aws_lambda = boto3.client('lambda')

parser = argparse.ArgumentParser(description="Upload an XPI and cause it to be signed.")
parser.add_argument('-t', '--type', help="Type of XPI (system or privileged)",
                    choices=['system', 'privileged'], required=True)
parser.add_argument('-s', '--s3-source', nargs='?',
                    help='S3 bucket to upload XPI to for signing')
parser.add_argument('xpi_file', type=file, help="Filename of XPI to sign")


def main(args=sys.argv[1:]):
    parameters = parser.parse_args(args)

    xpi_file = parameters.xpi_file
    xpi_sha256 = sha256(xpi_file)
    xpi_file.seek(0)
    bucket_name = parameters.s3_source or DEFAULT_S3_BUCKET
    bucket = s3.Bucket(bucket_name)
    key = os.path.basename(xpi_file.name)
    bucket.put_object(Body=xpi_file, Key=key)

    function_name = 'addons_sign-xpi-{}'.format(parameters.type)
    lambda_args = {
        "source": {
            "bucket": bucket_name,
            "key": key,
        },
        "checksum": xpi_sha256,
    }

    ret = aws_lambda.invoke(
        FunctionName=function_name,
        Payload=json.dumps(lambda_args)
    )

    if ret['StatusCode'] >= 300 or 'FunctionError' in ret:
        print("Invoking lambda failed")
        raw_response = ret['Payload'].read()
        try:
            response = json.loads(raw_response)
        except Exception as e:
            print("Couldn't parse response: {} {}".format(e, raw_response))
        else:
            if 'stackTrace' in response:
                tb_out = ''.join(traceback.format_list(response['stackTrace']))
                print(tb_out.rstrip('\n'))
            error_type = response.get('errorType', "No error type")
            error_msg = response.get('errorMessage')
            error_out = error_type
            if error_msg:
                error_out = '{}: {}'.format(error_type, error_msg)
            print(error_out)

        return 1

    print(ret['Payload'].read())
    return 0


def sha256(xpi_file):
    h = hashlib.sha256()
    h.update(xpi_file.read())
    return h.hexdigest()
