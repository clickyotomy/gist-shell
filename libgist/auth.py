#! /usr/bin/env python2.7

'''
Authentication modules for GitHub OAuth2 (not the web flow).
Perform CRUD operations on access tokens; authenticate users.
Common arguments:
    # username: GitHub username.
    # password: GitHub password.
    # _otp: One Time Password (X- GitHub-OTP) if 2fa
            (two factor authentication) is enabled.
    # _url: Custom API endpoint.
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


def create_authorization(username, password, _otp=None, _url=None):
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


def get_authorization(username, password, _id=None, _otp=None, _url=None):
    '''
    Get all the authorizations created using libgist (note: gist-shell).
    Lists a specific authorization if the '_id' argument is passed.
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
        if _id is not None:
            authorizations.append(data)
        else:
            for authorization in data:
                if str(authorization['note']) == 'gist-shell':
                    authorizations.append(authorization)

    return authorizations


def delete_authorization(username, password, _id=None, _otp=None, _url=None):
    '''
    Delete all the authorizations created using libgist (note: gist-shell).
    Delete a specific authorization if the '_id' argument is passed.
    '''
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
    else:
        authorizations = get_authorization(username, password)

    if len(authorizations) > 0:
        for auth in authorizations:
            auth_url = '/'.join([url, str(auth['id'])])
            requests.delete(auth_url, headers=headers,
                            auth=(username, password))
    else:
        requests.delete(url, headers=headers, auth=(username, password))
