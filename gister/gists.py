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

# Default API URL.
GITHUB_API_URL = 'https://api.github.com'

# Common headers.
GIST_HEADER = {
    'Accept': ('application/vnd.github.v3.raw+json,'
               'application/vnd.github.v3.base64+json'),
}


def parse_link_header(page, expression):
    '''
    Helper method for check_page_limit.
    '''
    if re.search(r'rel\=\"{0}\"'.format(expression), page):
        link = page.split(';')[0].strip()
        limit = re.search(r'\&page=(?P<limit>\d+)\>', link)
        return int(limit.groups()[0]) if limit is not None else limit


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
        return parse_link_header(page, 'next')


def list_gist(token=None, user=None, **kwargs):
    '''
    List Gists. If 'user' is specified, lists public gists for that user.
    If authenticated (by passing the access token), it returns the public
    Gists of that user.
    per_page: Number of results per page.
    page_limit: Fetch results upto this page.
    since: Timestamp in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ.
    starred: Return starred Gists of the authenticated user.
             An empty list will both username and token is passed.
    '''
    pages = []
    api = kwargs['api'] if 'api' in kwargs else None
    since = kwargs['since'] if 'since' in kwargs else None
    starred = kwargs['starred'] if 'starred' in kwargs else False
    per_page = kwargs['per_page'] if 'per_page' in kwargs else 100
    page_limit = kwargs['page_limit'] if 'page_limit' in kwargs else 2

    url = GITHUB_API_URL if api is None else api.rstrip('/')
    params = {'per_page': per_page, 'since': since} \
        if since is not None else {'per_page': per_page}

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
        if token is not None and user is None:
            url = '/'.join([url, 'starred'])
        else:
            return []

    current = 1

    while current <= page_limit:
        params.update({'page': current})
        response = requests.get(url, headers=GIST_HEADER, params=params)
        if response.status_code == 200:
            try:
                pages.extend(response.json())
            except (KeyError, ValueError):
                return []
        else:
            return []

        limit = check_page_limit(response)
        if limit is None:
            break
        current += 1

    return pages


def get_gist(token, gist_id, revison=None, api=None):
    '''
    Get a Gist (a particular version if it) based on it's ID.
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    if gist_id is None:
        return {}

    url = '/'.join([url, 'gists', str(gist_id)])

    if revison is not None:
        url = '/'.join([url, revison])

    response = requests.get(url, headers=GIST_HEADER)
    try:
        return response.json()
    except (KeyError, ValueError):
        return {}


def post_gist(token, files, description=None, public=False, api=None):
    '''
    Post a Gist.
    'files' should be a dictionary object, in the following format.
    files = {
        'filename': {
            'content': 'foo'
        }
        ...,
        ...,
    }
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    payload = json.dumps({
        'description': description,
        'public': public,
        'files': files
    })
    url = '/'.join([url, 'gists'])
    response = requests.post(url, data=payload, headers=GIST_HEADER)
    try:
        return response.json()
    except (KeyError, ValueError):
        return {}


def update_gist(token, gist_id, files, description, api=None):
    '''
    Update a gist.
    'files' shoud be a dictionary object, in the following format.
    files = {
        'file1.txt': {
            'content': 'updated file contents'
        },
        'old_name.txt': {
            'filename': 'new_name.txt',
            'content': 'modified contents'
        },
        'new_file.txt": {
            'content': 'a new file'
        },
        'delete_this_file.txt': None
    }
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    payload = json.dumps({
        'description': description,
        'files': files
    })
    url = '/'.join([url, 'gists', gist_id])
    response = requests.patch(url, data=payload, headers=GIST_HEADER)
    try:
        return response.json()
    except (KeyError, ValueError):
        return {}


def list_commits(token, gist_id, **kwargs):
    '''
    Return a list of the Gist commits.
    '''
    api = kwargs['api'] if 'api' in kwargs else None
    per_page = kwargs['per_page'] if 'per_page' in kwargs else 100
    page_limit = kwargs['page_limit'] if 'page_limit' in kwargs else 2

    commits = list()
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    url = '/'.join([url, 'gists', gist_id, 'commits'])
    current = 1
    params = {
        'per_page': per_page,
    }

    while current <= page_limit:
        params.update({'page': current})
        response = requests.get(url, headers=GIST_HEADER, params=params)
        if response.status_code == 200:
            try:
                commits.extend(response.json())
            except (KeyError, ValueError):
                return []
        else:
            return []

        limit = check_page_limit(response)

        if limit is None:
            break

        current += 1

    return commits


def star_gist(token, gist_id, flag=None, api=None):
    '''
    Star (or un-star) a Gist on GitHub.
    flag: True - star, False - un-star, None - get 'star' status.
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    GIST_HEADER.update({'Content-Length': 0})
    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    url = '/'.join([url, 'gists', gist_id, 'star'])

    if flag is True:
        response = requests.put(url, headers=GIST_HEADER)
    elif flag is False:
        response = requests.delete(url, headers=GIST_HEADER)
    else:
        response = requests.get(url, headers=GIST_HEADER)
        return True if response.status_code == 204 else False


def fork_gist(token, gist_id, api=None):
    '''
    Fork a Gist.
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    url = '/'.join([url, 'gists', gist_id, 'forks'])
    response = requests.post(url, headers=GIST_HEADER)
    try:
        return response.json()
    except (KeyError, ValueError):
        return {}


def list_forks(token, gist_id, **kwargs):
    '''
    Return a list of the Gist forks.
    '''
    api = kwargs['api'] if 'api' in kwargs else None
    per_page = kwargs['per_page'] if 'per_page' in kwargs else 100
    page_limit = kwargs['page_limit'] if 'page_limit' in kwargs else 2

    forks = list()
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    url = '/'.join([url, 'gists', gist_id, 'forks'])
    current = 1
    params = {
        'per_page': per_page,
    }

    while current <= page_limit:
        params.update({'page': current})
        response = requests.get(url, headers=GIST_HEADER, params=params)
        if response.status_code == 200:
            try:
                forks.extend(response.json())
            except (KeyError, ValueError):
                return []
        else:
            return []

        limit = check_page_limit(response)

        if limit is None:
            break

        current += 1

    return forks


def delete_gist(token, gist_id, api=None):
    '''
    Delete a gist.
    '''
    url = GITHUB_API_URL if api is None else api.rstrip('/')

    if token is not None:
        GIST_HEADER.update({'Authorization': ' '.join(['token', token])})

    url = '/'.join([url, 'gists', gist_id])
    response = requests.delete(url, headers=GIST_HEADER)

    if response.status_code == 204:
        return True

    return False
