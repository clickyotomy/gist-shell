#! /usr/bin/env python2.7

'''
Authentication modules for GitHub OAuth2 (not the web flow).
Perform CRUD operations on access tokens; authenticate users.
'''

import json
from time import time
from hashlib import sha1
from socket import getfqdn
from getpass import getuser

import requests


def generate_fingerprint():
    '''
    Generate a new fingerprint for tracking authorizations.
    '''
    details = '; '.join([getuser(), getfqdn()])
    timestamp = str(int(time()))
    hashed = sha1('-'.join([details, timestamp])).hexdigest()
    fingerprint = '; '.join([hashed, details, timestamp])

    return fingerprint


def generate_new_token(username, password, _otp=None, _url=None):
    '''
    Create a new authorization.
    '''
    payload = {
        'note': 'gist-shell-token',
        'scopes': ['gist'],
        'fingerprint': generate_fingerprint()
    }
    headers = {
        'Accept': 'application/vnd.github.damage-preview+json'
    }

    if _otp is not None:
        headers.update({'X-GitHub-OTP': _otp})

    if _url is not None:
        url = '/'.join([_url, 'authorizations'])
    else:
        url = 'https://api.github.com/authorizations'

    response = requests.post(url, headers=headers, data=json.dumps(payload),
                             auth=(username, password))
    return response
