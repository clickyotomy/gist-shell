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
    url = 'https://api.github.com/authorizations'
    payload = {
        'note': 'gist-shell',
        'note_url': 'https://github.com/clickyotomy/gist-shell',
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

    response = requests.post(url, headers=headers, data=json.dumps(payload),
                             auth=(username, password))

    return response.json()


def get_authorizations(username, password, _otp=None, _url=None, _id=None):
    '''
    Get all the authorizations created using libgist (note: gist-shell).
    '''
    authorizations = list()
    url = 'https://api.github.com/authorizations'
    headers = headers = {
        'Accept': 'application/vnd.github.damage-preview+json'
    }

    if _otp is not None:
        headers.update({'X-GitHub-OTP': _otp})

    if _url is not None:
        url = '/'.join([_url, 'authorizations'])

    if _id is not None:
        url = '/'.join([url, _id])

    response = requests.get(url, auth=(username, password), headers=headers)

    if response.status_code == 200:
        data = response.json()
        for authorization in data:
            if str(authorization['note']) == 'gist-shell':
                authorizations.append(authorization)

    return authorizations
