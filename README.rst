==========
 sign-xpi
==========

An AWS Lambda (and a supplementary CLI utility) to sign XPI files.

The packaging of this repository is meant to be reminiscent of the
amo2kinto-lambdo repo.

Use this script to generate a zip for Amazon Lambda::

  make clean virtualenv zip

You must run this script on a linux x86_64 arch, the same as Amazon Lambda.

This will package a lambda with a handler at ``aws_lambda.sign_xpi.handle``.

Development
===========

Another virtualenv is created for doing development, so that we don't
accidentally include dev tools in the lambda. To build it::

  make virtualenv-dev

Run the tests using::

  . .venv-dev/bin/activate
  py.test
