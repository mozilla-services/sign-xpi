"""Fake setup.py for "parent" package of the lambda and anything else."""

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as changelog_file:
    changelog = changelog_file.read()

setup(
    name='sign_xpi-parent',
    version='0.1.1.dev0',
    description='Fake parent package for the sign-xpi lambda',
    long_description=readme + '\n\n' + changelog,
    author="Product Delivery Team",
    author_email="storage-team@mozilla.com",
    url='https://github.com/mozilla-services/sign-xpi',
    license="MPL",
    keywords='sign_xpi',
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
    zip_safe=False,
)
