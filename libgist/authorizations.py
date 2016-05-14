#! /usr/bin/env python2.7

'''
Authentication modules for GitHub OAuth2 (not the web flow).
Create, fetch, delete authorizations; authenticate users.
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
    hashed = sha1('--'.join([details, timestamp])).hexdigest()
    fingerprint = '; '.join([hashed, details, timestamp])

    return fingerprint


def github_auth_request(http, uri, auth=(), **kwargs):
    '''
    Generic method to make authorized HTTP requests to GitHub.
    method: The HTTP method.
    auth: GitHub credentials (username, password) for HTTP Basic Auth.
    payload: The request payload, in JSON.
    otp: If 2fa (Two Factor Authentication) enabled, the One Time Password.
    api: API URL for non GitHub endpoints (e.g.: GitHub Enterprise),
         excluding the trailing slash.
    '''
    otp = kwargs['otp']
    api = kwargs['api']
    payload = kwargs['payload']
    api_url = 'https://api.github.com/authorizations'
    headers = {
        'Accept': 'application/vnd.github.damage-preview+json'
    }

    url = api_url if api is not None else api

    if otp is not None:
        headers.update({'X-GitHub-OTP': otp})

    if uri is not None:
        url = '/'.join([url, uri])

    request = getattr(requests, http)
    response = request(url, data=payload, auth=auth, headers=headers)

    return response


def create_authorization(auth, otp=None, api=None):
    '''
    Create a new authorization.
    '''
    payload = json.dumps({
        'note': 'gist-shell',
        'note_url': 'https://github.com/clickyotomy/gist-shell',
        'scopes': ['gist'],
        'fingerprint': generate_fingerprint()
    })

    response = github_auth_request(http='post', uri=None, auth=auth,
                                   payload=payload, otp=otp, api=api)

    return response.json()


def get_authorization(auth, auth_ids=None, otp=None, api=None):
    '''
    Get all the authorizations created using libgist (note: gist-shell).
    List specific authorization(s) if the 'auth_ids' argument is passed.
    '''
    authorizations = list()

    if auth_ids is None or len(auth_ids) <= 0:
        response = github_auth_request(http='get', uri=None, auth=auth,
                                       payload='{}', otp=otp, api=api)
        if response.status_code == 200:
            data = response.json()
            for authorization in data:
                if str(authorization['note']) == 'gist-shell':
                    authorizations.append(authorization)

    else:
        for auth_id in auth_ids:
            response = github_auth_request(http='get', uri=auth_id, auth=auth,
                                           payload='{}', otp=otp, api=api)

            if response.status_code == 200:
                data = response.json()
                if str(data['note']) == 'gist-shell':
                    authorizations.append(data)
    return authorizations


def delete_authorization(auth, auth_ids=None, otp=None, api=None):
    '''
    Delete all the authorizations created using libgist (note: gist-shell).
    Delete specific authorization(s) if the 'auth_ids' argument is passed.
    '''
    authorizations = get_authorization(auth=auth, auth_ids=auth_ids, otp=otp,
                                       api=api)

    for authorization in authorizations:
        auth_id = str(authorization['id'])
        github_auth_request(http='delete', uri=auth_id, auth=auth,
                            payload='{}', otp=otp, api=api)
