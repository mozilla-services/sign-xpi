#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='sign-xpi',
    version='0.1.0',
    description="A thin CLI wrapper around the sign-xpi lambda",
    long_description=readme,
    author="Team Afterburner",
    author_email='storage-team@mozilla.com',
    url='https://github.com/mozilla-services/addon-shipping',
    packages=[
        'addon_shipping_cli',
    ],
    package_dir={'addon_shipping_cli':
                 'addon_shipping_cli'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "sign-xpi = addon_shipping_cli.__main__:sign_xpi"
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
