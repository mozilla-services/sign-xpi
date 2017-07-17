import io
import pytest
import marshmallow.exceptions
from aws_lambda import sign_xpi


def test_get_extension_id_rdf_sanity_check():
    simple_rdf = io.StringIO("""<?xml version="1.0" encoding="UTF-8"?>

<RDF xmlns="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:em="http://www.mozilla.org/2004/em-rdf#">
  <Description about="urn:mozilla:install-manifest">
    <em:id>hypothetical-addon@mozilla.org</em:id>
  </Description>
</RDF>""")
    extension_id = sign_xpi.get_extension_id_rdf(simple_rdf)

    assert extension_id == 'hypothetical-addon@mozilla.org'


def test_parse_s3_event_success():
    raw_s3_event = {
        "Records": [
            {
                "eventVersion":"2.0",
                "eventSource":"aws:s3",
                "awsRegion":"us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName":"ObjectCreated:Put",
                "userIdentity":{
                    "principalId":"Amazon-customer-ID-of-the-user-who-caused-the-event"
                },
                "requestParameters":{
                    "sourceIPAddress":"ip-address-where-request-came-from"
                },
                "responseElements":{
                    "x-amz-request-id":"Amazon S3 generated request ID",
                    "x-amz-id-2":"Amazon S3 host that processed the request"
                },
                "s3":{
                    "s3SchemaVersion":"1.0",
                    "configurationId":"ID found in the bucket notification configuration",
                    "bucket":{
                        "name":"mybucket",
                        "ownerIdentity":{
                            "principalId":"Amazon-customer-ID-of-the-bucket-owner"
                        },
                        "arn":"bucket-ARN"
                    },
                    "object":{
                        "key":"HappyFace.jpg",
                        "size":1024,
                        "eTag":"d41d8cd98f00b204e9800998ecf8427e",
                        "versionId":"096fKKXTRTtl3on89fVO.nfljtsv6qko",
                        "sequencer":"0055AED6DCD90281E5"
                    }
                }
            },
        ]
    }
    s3_event = sign_xpi.S3Event(strict=True).load(raw_s3_event).data
    assert s3_event == {
        'records': [
            {
                's3': {
                    'bucket': {
                        'name': 'mybucket',
                    },
                    'object': {
                        'key': 'HappyFace.jpg',
                    }
                }
            }
        ]
    }


def test_parse_s3_event_fails_when_missing_s3():
    raw_s3_event = {
        "Records": [
            {
                "eventVersion":"2.0",
                "eventSource":"aws:s3",
                "awsRegion":"us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName":"ObjectCreated:Put",
                "userIdentity":{
                    "principalId":"Amazon-customer-ID-of-the-user-who-caused-the-event"
                },
                "requestParameters":{
                    "sourceIPAddress":"ip-address-where-request-came-from"
                },
                "responseElements":{
                    "x-amz-request-id":"Amazon S3 generated request ID",
                    "x-amz-id-2":"Amazon S3 host that processed the request"
                },
                "s4":{
                    "s3SchemaVersion":"1.0",
                    "configurationId":"ID found in the bucket notification configuration",
                    "bucket":{
                        "name":"mybucket",
                        "ownerIdentity":{
                            "principalId":"Amazon-customer-ID-of-the-bucket-owner"
                        },
                        "arn":"bucket-ARN"
                    },
                    "object":{
                        "key":"HappyFace.jpg",
                        "size":1024,
                        "eTag":"d41d8cd98f00b204e9800998ecf8427e",
                        "versionId":"096fKKXTRTtl3on89fVO.nfljtsv6qko",
                        "sequencer":"0055AED6DCD90281E5"
                    }
                }
            },
        ]
    }
    with pytest.raises(marshmallow.exceptions.ValidationError):
        sign_xpi.S3Event(strict=True).load(raw_s3_event).data


def test_verify_extension_id_sanity_check():
    event = {'s3': {'object': {'key': 'test-pilot@mozilla.com/build-20170715.xpi'}}}
    sign_xpi.verify_extension_id(event, 'test-pilot@mozilla.com')


def test_verify_extension_id_enforces_match():
    event = {'s3': {'object': {'key': 'devtools@mozilla.com/build-20170715.xpi'}}}
    with pytest.raises(sign_xpi.S3IdMatchError):
        sign_xpi.verify_extension_id(event, 'test-pilot@mozilla.com')


def test_verify_extension_id_handles_missing_id():
    event = {'s3': {'object': {'key': 'build-20170715.xpi'}}}
    with pytest.raises(sign_xpi.S3IdNotPresentError):
        sign_xpi.verify_extension_id(event, 'test-pilot@mozilla.com')
