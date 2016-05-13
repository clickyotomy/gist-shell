#! /usr/bin/env python2.7

'''
Perform CRUD operations on GitHub Gists.
Common arguments to all fucnctions:
    1. token: The access token for the API.
    2. api: API URL for the endpoint, other than GitHub.
'''

import re
import json
import requests

# For testing only.
VAULT = json.loads(open('vault/login.json', 'r').read())
LOGIN = (VAULT['username'], VAULT['password'])
GH_TOKEN = VAULT['gh_token']
GHE_TOKEN = VAULT['ghe_token']

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
    if 'Link' in headers:
        page_metadata = headers['Link'].split(', ')
    else:
        return None

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
    per_page: Number of results per page.
    page_limit: Fetch results upto this page.
    since: Timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
    starred: Return starred gists of the authenticated user.
    '''
    pages = []
    api = kwargs['api'] if 'api' in kwargs else None
    since = kwargs['since'] if 'since' in kwargs else None
    starred = kwargs['starred'] if 'starred' in kwargs else False
    per_page = kwargs['per_page'] if 'per_page' in kwargs else 100
    page_limit = kwargs['page_limit'] if 'page_limit' in kwargs else 2

    url = GITHUB_API_URL if api is None else api.rstrip('/')
    params = {
        'per_page': per_page,
    }

    if since is not None:
        params.update({'since': since})

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    if user is None:
        if token is None:
            url = '/'.join([url, 'gists', 'public'])
        else:
            url = '/'.join([url, 'gists'])

    else:
        url = '/'.join([url, 'users', user, 'gists'])

    if starred:
        url = '/'.join([url, 'starred'])

    current = 1
    check_flag = False

    while current <= page_limit:
        params.update({'page': current})
        response = requests.get(url, headers=GIST_HEADER, params=params)
        if response.status_code == 200:
            pages.extend(response.json())
        else:
            return []

        if check_flag is False:
            limit = check_page_limit(response)
            if limit is not None:
                if page_limit > limit:
                    page_limit = limit
            else:
                page_limit = 2
            check_flag = True
        current += 1

    return pages
