sign_xpi
========

This function is responsible for "signing" an XPI for a system or privileged addon. This means taking a plain, unsigned
system or privileged addon, and adding a signature to it. The signature is provided by `Autograph
<https://github.com/mozilla-services/autograph/>`_, the Mozilla keyring service.

Input
=====

This lambda expects a context which should provide this information:

.. code-block:: json

    {
        "autograph": {
            "serverUrl": "http://some.server.example/",
            "hawkId": "hawk-id-for-autograph",
            "hawkSecret": "hawk-secret-for-autograph",
            "keyId": "autograph-signer-key-id"
        },
        "outputBucket": "some-s3-bucket"
    }

The lambda is designed to sign only one category of addons: either system addons, or privileged extensions. To sign
both, deploy the lambda twice with two sets of Autograph credentials.

A "sign event" is taken as input, which should conform to this format:

.. code-block:: json

    {
        "source": {
            "bucket": "aws-s3-bucket",
            "key": "some-xpi-filename.xpi"
        },
        "checksum": "sha256 of the object specified by source"
    }

As an alternative to passing an S3 bucket/key in the source, you can also pass a ``"url"`` field, which will be fetched by the lambda.

Output
======

The lambda will sign the XPI and upload it to the S3 bucket specified in its context. (N.B. that you cannot change this bucket, because signing any XPI whatsoever is safe only if access to signed XPIs is trusted.) The return value of this lambda will be an object like:

.. code-block:: json

    {
        "bucket": "s3-output-bucket",
        "key": "some-xpi-filename.xpi"
    }

Outstanding questions
=====================

- [ ] How does this lambda decide to use the signature/key for privileged extensions, vs. system addons?
- [ ] What format is mozilla.rsa? Am I handling it correctly from Autograph?
