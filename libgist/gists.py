#! /usr/bin/env python2.7

'''
Perform CRUD operations on GitHub Gists.
'''

import re
import json
import requests

# For testing only.
VAULT = json.loads(open('vault/login.json', 'r').read())
LOGIN = (VAULT['username'], VAULT['password'])
TOKEN = VAULT['token']

# Default API URL.
GITHUB_API_URL = 'https://api.github.com'

# Common headers.
GIST_HEADER = {
    'Accept': 'application/vnd.github.VERSION.raw+json',
}


def check_page_limit(response):
    '''
    Check how many pages are available in the Gist listing.
    '''
    headers = response.headers
    page_metadata = headers['Link'].split(', ')

    for page in page_metadata:
        if re.search(r'rel\=\"last\"', page):
            link = page.split(';')[0].strip()
            limit = re.search(r'\&page=(?P<limit>\d+)\>', link)
            return int(limit.groups()[0]) if limit is not None else limit


def list_gists(user=None, token=None, **kwargs):
    '''
    List gists. If 'user' is specified, lists public gists for that user.
    If authenticated (by passing the access token), it returns the public
    gists of that user.
    '''
    pages = []
    api = kwargs['api'] if 'api' in kwargs else None
    since = kwargs['since'] if 'since' in kwargs else None
    per_page = kwargs['per_page'] if 'per_page' in kwargs else 100
    page_limit = kwargs['page_limit'] if 'page_limit' in kwargs else 2

    url = GITHUB_API_URL if api is None else api
    params = {
        'per_page': per_page,
    }

    if since is not None:
        params.update({'since': since})

    if user is None:
        url = '/'.join([url, 'gists'])
        if token is not None:
            GIST_HEADER.update({'Authorization': ' '.join(['token', token])})
    else:
        url = '/'.join([url, 'users', user, 'gists'])

    current = 1
    check_flag = False

    while current <= page_limit:
        params.update({'page': current})
        response = requests.get(url, headers=GIST_HEADER, params=params)
        if response.status_code == 200:
            pages.extend(response.json())
        if check_flag is False:
            limit = check_page_limit(response)
            if limit is not None and page_limit > limit:
                page_limit = limit
            check_flag = True
        current += 1

    return pages
