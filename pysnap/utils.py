# -*- coding: utf-8 -*-

"""
    This module contains methods for creating request tokens and
    encryption/decryption of snaps
"""

from hashlib import sha256
from time import time
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import requests
from proxyscrape import *

URL = 'https://accounts.snapchat.com/'
AUTH_URL = 'https://accounts.snapchat.com/'

SECRET = b'iEk21fuwZApXlz93750dmW22pw389dPwOk'
STATIC_TOKEN = 'm198sOkJEn37DjqZ32lpRu76xmw288xSQ9'
BLOB_ENCRYPTION_KEY = 'M02cnQ51Ji97vwT4'
HASH_PATTERN = ('00011101111011100011110101011110'
                '11010001001110011000110001000110')


def make_request_token(a, b):
    hash_a = sha256(SECRET + a.encode('utf-8')).hexdigest()
    hash_b = sha256(b.encode('utf-8') + SECRET).hexdigest()
    return ''.join((hash_b[i] if c == '1' else hash_a[i]
                    for i, c in enumerate(HASH_PATTERN)))


def get_token(auth_token=None):
    return STATIC_TOKEN if auth_token is None else auth_token


def pkcs5_pad(data, blocksize=16):
    pad_count = blocksize - len(data) % blocksize
    return data + (chr(pad_count) * pad_count).encode('utf-8')


def decrypt(data):
    cipher = Cipher(algorithms.AES(BLOB_ENCRYPTION_KEY), modes.ECB(),
                    backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(pkcs5_pad(data)) + decryptor.finalize()


def decrypt_story(data, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                    backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(pkcs5_pad(data)) + decryptor.finalize()


def encrypt(data):
    cipher = Cipher(algorithms.AES(BLOB_ENCRYPTION_KEY), modes.ECB(),
                    backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(pkcs5_pad(data)) + encryptor.finalize()


def timestamp():
    return int(round(time() * 1000))

# Proxy Rotation
collector = create_collector('scrape', ['http', 'https'])
proxy = collector.get_proxy({'code': 'us', 'anonymous': True})

def proxy_refresh(proxy):
    collector.refresh_proxies(force=True)
    proxy = collector.get_proxy({'code': ('us'), 'anonymous': True})
    return proxy


def request(endpoint, auth_token, data=None, files=None,
            raise_for_status=True, req_type='post', proxies=proxy):
    """Wrapper method for calling Snapchat API which adds the required auth
    token before sending the request.

    :param endpoint: URL for API endpoint
    :param data: Dictionary containing form data
    :param raise_for_status: Raise exception for 4xx and 5xx status codes
    :param req_type: The request type (GET, POST). Defaults to POST
    """
    now = timestamp()
    if data is None:
        data = {}
    headers = {
        'User-Agent': 'Snapchat/9.2.0.0 (A0001; '
                      'Android 4.4.4#5229c4ef56#19; gzip)',
        'Accept-Language': 'en-US;q=1, en;q=0.9',
        'Accept-Locale': 'en'
    }

    if endpoint == 'login':
        url = AUTH_URL + 'accounts/'
    else:
        url = URL + 'accounts'

    if req_type == 'post':
        data.update({
            'timestamp': now,
            'req_token': make_request_token(auth_token or STATIC_TOKEN,
                                            str(now))
        })
        r = requests.post(url + endpoint, data=data, files=files,
                          headers=headers, proxies=proxies)
    else:
        r = requests.get(url + endpoint, params=data, headers=headers, proxies=proxies)
    # if raise_for_status:
    #     r.raise_for_status()
    # print(type(r))
    if "429" in str(r):
        return "overload"
    return r


def make_media_id(username):
    """Create a unique media identifier. Used when uploading media"""
    return '{username}~{uuid}'.format(username=username.upper(),
                                      uuid=str(uuid4()))
