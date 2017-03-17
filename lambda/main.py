"""
sign-xpi: Sign an XPI file
"""

import os.path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "site-packages"))

import logging
import requests


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handle(event, context):
    """
    Lambda handler
    """
    logger.info("%s - %s", event, context)

    url = "https://api.ipify.org?format=json"

    raw = requests.get(url)
    logger.info("%s", raw)
    result = raw.json()

    logger.info("Lambda IP: %s", result['ip'])

    return event
