import json
import os.path
import time
from pysnap.utils import (
    encrypt, decrypt, decrypt_story, make_media_id, request, proxy, proxy_refresh
)

MEDIA_IMAGE = 0
MEDIA_VIDEO = 1
MEDIA_VIDEO_NOAUDIO = 2

FRIEND_CONFIRMED = 0
FRIEND_UNCONFIRMED = 1
FRIEND_BLOCKED = 2
PRIVACY_EVERYONE = 0
PRIVACY_FRIENDS = 1


def is_video(data):
    return len(data) > 1 and data[0:2] == b'\x00\x00'


def is_image(data):
    return len(data) > 1 and data[0:2] == b'\xFF\xD8'


def is_zip(data):
    return len(data) > 1 and data[0:2] == b'PK'


def get_file_extension(media_type):
    if media_type in (MEDIA_VIDEO, MEDIA_VIDEO_NOAUDIO):
        return 'mp4'
    if media_type == MEDIA_IMAGE:
        return 'jpg'
    return ''


def get_media_type(data):
    if is_video(data):
        return MEDIA_VIDEO
    if is_image(data):
        return MEDIA_IMAGE
    return None


def _map_keys(snap):
    return {
        u'id': snap.get('id', None),
        u'media_id': snap.get('c_id', None),
        u'media_type': snap.get('m', None),
        u'time': snap.get('t', None),
        u'sender': snap.get('sn', None),
        u'recipient': snap.get('rp', None),
        u'status': snap.get('st', None),
        u'screenshot_count': snap.get('c', None),
        u'sent': snap.get('sts', None),
        u'opened': snap.get('ts', None)
    }


class Snapchat(object):
    """Construct a :class:`Snapchat` object used for communicating
    with the Snapchat API.

    Usage:

        from pysnap import Snapchat
        snapchat = Snapchat()
        snapchat.login('username', 'password')
        ...

    """

    # Initialize proxy
    proxy = proxy_refresh(proxy)

    def __init__(self, proxy):
        self.username = None
        self.auth_token = None
        self.proxy = proxy

    def _request(self, endpoint, proxies=proxy, data=None, files=None, raise_for_status=True, req_type='post'):
        return request(endpoint, self.auth_token, data, files, raise_for_status, proxies, req_type)

    def _unset_auth(self):
        self.username = None
        self.auth_token = None

    def login(self, username, password):
        self._unset_auth()
        r = self._request('login', {
            'username': username,
            'password': password
        })
        result = r.content

        # Proxy Dead
        if r == "overload":
            print(f" [ ! | PROXY ] EXPIRED! ROTATING!\n [ ! | PASSWORD] Last attempt: {password}" + "\n")
            time.sleep(1)

            # Refresh Proxy
            proxy_refresh(proxy)
            print(" [ ! | PROXY ] Rotated.")
            time.sleep(3)
            pass

        if b'updates_response' in result:
            if 'auth_token' in result['updates_response']:
                self.auth_token = result['updates_response']['auth_token']
            if 'username' in result['updates_response']:
                self.username = username

        return result
