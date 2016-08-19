#! /usr/bin/env python2.7

'''
gist.py: A simple command line interface for creating, fetching, browsing,
           updating and deleting Gists on GitHub.
'''

import os
import sys
import json
import socket
import getpass

# Try importing the library during development.
try:
    import imp
    imp.find_module('gister')
except ImportError:
    PATH = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(PATH)))

# Should work, if the library is already installed.
from gister import (authorizations, gists)


# Default path to store credentials locally.
DEAFULT_CREDENTIALS_PATH = '/'.join([os.path.expanduser('~'),
                                     '.gist-shell', 'vault.json'])


# For colorama.
# from colorama import init, Fore, Back, Style
# init(autoreset=True)


def get_external_ip_addr():
    '''
    Get the external IP address of the host.
    '''
    try:
        _sockets = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sockets.connect(("github.com", 80))
        _socket_name = _sockets.getsockname()[0]
        _sockets.close()
    except socket.error:
        # Fallback option.
        return socket.getfqdn()
    return _socket_name


def fetch_credentials(path=DEAFULT_CREDENTIALS_PATH, fetch=None):
    '''
    Fetch the credentials from the vault.

    Caveats:
        1. When 'fetch' is None, it loads the default set of credentials.
        2. If a duplicate default exists, return the first one.
        3. If fetch is not set to None and the key doesn't exist,
           the function will return None.
    '''
    if os.path.exists(path):
        try:
            vault = json.loads(open(path, 'r').read())
            if fetch is None:
                for _ in vault.keys():
                    if vault[_]['default']:
                        return vault[_]['credentials']
            return vault[fetch]['credentials']
        except (ValueError, KeyError):
            return None
    return None


def update_credentials(data, name, path=DEAFULT_CREDENTIALS_PATH, force=False):
    '''
    Update the vault with payload.

    Caveats:
        1. If the payload has the default flag set, it checks against the
           all the stored credentials, if a duplicate exists, it unsets the
           flag on the duplicate.
        2. If the vault has a malformed JSON, the function will exit,
           returning None, if force is set to True, it will overwrite the
           vault with the new credentials.
        3. If the vault file has incorrect file permissions, the function
           will exit with by returning None.
        4. If a duplicate credential exists, the function will return a None;
           if force is set to True, it will update the existing credential.
    '''
    vault = {}
    if os.path.exists(path):
        try:
            vault = json.loads(open(path, 'r').read())
        except (KeyError, ValueError):
            vault = {}

    if name in vault.keys() and not force:
        return None

    if data[name]['default']:
        for _ in vault.keys():
            try:
                if vault[_]['default']:
                    vault[_].update({'default': False})
            except (KeyError, ValueError):
                if force:
                    vault = {}
                return None

    vault.update(data)

    try:
        with open(path, 'w') as _vault_file:
            _vault_file.write(json.dumps(vault, indent=4, sort_keys=True))
    except IOError:
        return None

    return vault


def login(path=DEAFULT_CREDENTIALS_PATH, api=None, default=False):
    '''
    Create an authorization (access token; scope: 'gist') on GitHub.
    Works with HTTP Basic Authentication (RFC-2617).

    Caveats:
        1. For username, hit return to user the login username.
        2. For github-2fa-auth, hit return to skip.
        3. 'gist-shell' will appended to auth-token-note for storing
           the description for the Personal Access Token.
    '''
    username = raw_input('github-username: ').strip()
    username = getpass.getuser() if len(username) < 1 else username
    password = getpass.getpass('github-password: ').strip()
    auth_2fa = raw_input('github-2fa-auth: ').strip()
    auth_2fa = None if len(auth_2fa) < 1 else auth_2fa
    token_note = raw_input('auth-token-note: ').strip()

    response = authorizations.create_authorization(auth=(username, password),
                                                   note=token_note,
                                                   otp=auth_2fa, api=api)
    if response[0]:
        data = response[1]
        print data
        to_write = {
            data['app']['name']: {
                'credentials': {
                    'id': data['id'],
                    'token': data['token'],
                    'username': username,
                    'created-at': data['created_at'],
                },
                'default': default
            }
        }
        update_credentials(data=to_write, name=data['app']['name'], path=path,
                           force=default)

        return True
    return False


def upload(payload, token, description=None, public=False, update=False):
    '''
    Upload the payload to GitHub.

    Caveats:
        1. The Gists are private by default.
        2. If no description is provided, a default string with the
           login username, hostname, IP adderss and time (in UTC) will
           be provided.
    '''
    pass
