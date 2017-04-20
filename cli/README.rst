This is a thin wrapper around the sign-xpi lambda.

Usage::

  $ sign-xpi -t [privileged|system] file.xpi
  {"uploaded": {"bucket": "some-s3-bucket", "key": "file.xpi"}}

Because of the limitation that Amazon Lambdas can only handle a
relatively constrained request body, ``sign-xpi`` begins by uploading
the XPI to S3. A default S3 bucket is hard-coded, but you can specify
the S3 bucket using the ``-s`` or ``--s3-source`` argument.

This program needs AWS access in order to run. We use boto3 for this
access, so you may need to `configure
<https://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration>`_
it to tell it about your credentials.
