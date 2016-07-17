#! /usr/bin/env python2.7

'''
Authentication modules for GitHub OAuth2 (not the web flow).
Create, fetch, delete authorizations; authenticate users.
'''

import re
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

    url = api_url if api is not None else api_url

    if otp is not None:
        headers.update({'X-GitHub-OTP': otp})

    if uri is not None:
        url = '/'.join([url, uri])

    request = getattr(requests, http)
    response = request(url, data=payload, auth=auth, headers=headers)

    return response


def create_authorization(auth, note='', otp=None, api=None):
    '''
    Create a new authorization.
    '''
    payload = {
        'note_url': 'https://github.com/clickyotomy/gist-shell',
        'scopes': ['gist'],
        'fingerprint': generate_fingerprint()
    }

    if len(note) > 1:
        note = re.sub('-', ' ', note.lower()).split(' ')
        default = ['gist-shell']
        default.extend(note)
        payload.update({'note': '-'.join(default)})

    else:
        payload.update({'note': 'gist-shell'})

    response = github_auth_request(http='post', uri=None, auth=auth,
                                   payload=json.dumps(payload), otp=otp,
                                   api=api)

    status = True if response.status_code == 201 else False
    try:
        return (status, response.json())
    except (KeyError, ValueError):
        return (status, None)


def get_authorization(auth, auth_ids=None, otp=None, api=None):
    '''
    Get all the authorizations created using gist-shell (note: gist-shell).
    List specific authorization(s) if the 'auth_ids' argument is passed.
    '''
    authorizations = list()

    if auth_ids is None or len(auth_ids) <= 0:
        response = github_auth_request(http='get', uri=None, auth=auth,
                                       payload='{}', otp=otp, api=api)
        if response.status_code == 200:
            try:
                data = response.json()
                for authorization in data:
                    if re.search('gist-shell', str(data['note'])):
                        authorizations.append(authorization)
            except (KeyError, ValueError):
                return []
    else:
        for auth_id in auth_ids:
            response = github_auth_request(http='get', uri=auth_id, auth=auth,
                                           payload='{}', otp=otp, api=api)

            if response.status_code == 200:
                try:
                    data = response.json()
                    if re.search('gist-shell', str(data['note'])):
                        authorizations.append(data)
                except (KeyError, ValueError):
                    return []
    return authorizations


def delete_authorization(auth, auth_ids=None, otp=None, api=None):
    '''
    Delete all the authorizations created using gist-shell (note: gist-shell).
    Delete specific authorization(s) if the 'auth_ids' argument is passed.
    '''
    authorizations = get_authorization(auth=auth, auth_ids=auth_ids, otp=otp,
                                       api=api)

    delete_count = 0
    for authorization in authorizations:
        auth_id = str(authorization['id'])
        response = github_auth_request(http='delete', uri=auth_id, auth=auth,
                                       payload='{}', otp=otp, api=api)
        if response.status_code == 204:
            delete_count += 1

    if delete_count == len(authorizations):
        return True

    return False
