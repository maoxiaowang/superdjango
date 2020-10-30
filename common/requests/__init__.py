"""
HOW TO USE:

class MySessionRequest(SessionRequest):
    base_url = 'http://127.0.0.1:8000'

    @SessionRequest.auth()
    def list_vm(self):
        return self.get('/vm')


class MyTokenRequest(TokenRequest):
    token_field_name = None

    def _get_token(self):
        return TOKEN-STRING

"""

import copy
import datetime
import functools

import requests
from django.core.validators import URLValidator
from requests.auth import HTTPBasicAuth
from django.core.cache import cache

from common.core.exceptions import ECloudException


__all__ = [
    'SessionRequest',
    'Token',
    'TokenRequest',
    'TokenExpiresAt',
    'BasicAuthRequest'
]


class AuthenticationFailed(ECloudException):
    pass


class RequestFailed(ECloudException):

    def __init__(self, code, msg=None, **kwargs):
        self.msg = msg or ''
        self.kwargs = kwargs
        self.code = code

    def __str__(self):
        return '[%s] %s' % (self.code, self.msg)


class Request(object):
    base_url = None
    default_headers = dict()

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        # assert isinstance(cls.base_url, str)
        if cls.base_url:
            URLValidator()(cls.base_url)
        assert isinstance(cls.default_headers, dict)
        return super_new(cls)

    def _full(self, url):
        if self.base_url:
            if not url.startswith('/'):
                url = '/' + url
            # return url_parse.urljoin(self.base_url, url)
            return self.base_url + url
        return url

    def get(self, url, params=None, **kwargs):
        raise NotImplementedError

    def post(self, url, data=None, **kwargs):
        raise NotImplementedError

    def put(self, url, data=None, **kwargs):
        raise NotImplementedError

    def delete(self, url, **kwargs):
        raise NotImplementedError


class SessionRequest(Request):
    session_timeout: int = 3600
    username: str = None
    password: str = None

    def __init__(self):
        self.session = requests.Session()
        self.last_login = None
        self._auth()

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        assert cls.username
        assert cls.password
        return super_new(cls)

    @staticmethod
    def auth():
        """
        Use for specific interface

        [example]
        def wrapper(func):

            @wraps(func)
            def inner(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                try:
                    res = json.loads(result.content)
                except json.decoder.JSONDecodeError:
                    if self._need_auth:
                        self._auth()
                        return inner(self, *args, **kwargs)
                    raise
                except Exception as e:
                    raise
                if res['code'] != '200':
                    raise RequestFailed(res['code'], res['msg'])
                return res

            return inner

        return wrapper
        """
        raise NotImplementedError

    @property
    def _need_auth(self):
        if self.last_login is None:
            self.last_login = datetime.datetime.now()
            return True
        return (datetime.datetime.now() - self.last_login).total_seconds() > self.session_timeout

    def _auth(self):
        """
        [example]
        data = {
            'username': self.username,
            'pwd': self.password,
        }
        result = self.session.post(self._full('/edmapiv2/login'), data=data, verify=False)
        res = json.loads(result.content)
        if res['code'] != '200':
            raise AuthenticationFailed
        self.last_login = datetime.datetime.now()   # DO NOT forget this step
        """
        raise NotImplementedError

    def get(self, url, params=None, **kwargs):
        return self.session.get(self._full(url), params=params, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.session.post(self._full(url), data=data, verify=False, **kwargs)

    def put(self, url, data=None, **kwargs):
        return self.session.put(self._full(url), data=data, verify=False, **kwargs)

    def delete(self, url, **kwargs):
        # res = self.session.delete(self._full_url(url), **kwargs)
        request = requests.Request('DELETE', self._full(url), **kwargs)
        prepared_request = self.session.prepare_request(request)
        settings = self.session.merge_environment_settings(prepared_request.url, None, None, False, None)
        return self.session.send(prepared_request, **settings)


class TokenExpiresAt:
    """
    Token Expires at Descriptor
    Describe token expires datetime (UTC)
    """
    key = '_token_expires_at'

    def __init__(self, key: str = None):
        if key:
            assert isinstance(key, str)
            self.key = key

    def __get__(self, instance, owner):
        return cache.get(self.key)

    def __set__(self, instance, value: datetime.datetime):
        total_seconds = (value - datetime.datetime.utcnow()).total_seconds()
        if total_seconds <= 0:
            cache.delete(self.key)
        else:
            cache.set(self.key, value, total_seconds)
        return value


class Token:
    """
    Token Descriptor
    no token/token expired --> get new token
    """
    key = '_token'
    expires_at = TokenExpiresAt()

    def get_token_and_expired_at(self) -> (str, datetime.datetime):
        """
        Must be return a tuple with a new token and expires time (UTC),
        e.g. ('xsRsm3fE2zzT53sup5k', datetime(2020, 4, 1, 10, 14, 33))
        """
        raise NotImplementedError

    def __init__(self, key=None):
        if key:
            assert isinstance(key, str)
            self.key = key

    def __get__(self, instance, owner):
        if self.expires_at is None:
            print('is None')
            self.__delete__(instance)
        token = cache.get(self.key)
        if token is None:
            self.expires_at = datetime.datetime.utcnow()
            token = self.__set__(instance, None)  # new token
        return token

    def __set__(self, instance, value):
        """
        Renew the token and expired_at
        """
        token, expires_at = self.get_token_and_expired_at()
        self.expires_at = expires_at
        valid_seconds = (expires_at - datetime.datetime.utcnow()).total_seconds()
        cache.set(self.key, token, valid_seconds)
        return token

    def __delete__(self, instance):
        cache.delete(self.key)


def append_headers(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        kwargs.update(headers=self._get_headers(kwargs.get('headers')))
        return func(self, *args, **kwargs)

    return wrapper


class TokenRequest(Request):
    token_field_name = None
    token = Token()

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        assert cls.token_field_name
        return super_new(cls)

    def _get_token(self):
        return self.token

    def _get_headers(self, default_headers=None):
        headers = copy.deepcopy(default_headers or self.default_headers)
        token = self._get_token()
        headers.update({'Content-Type': 'application/json'})
        headers.update({self.token_field_name: token})
        return headers

    @append_headers
    def get(self, url, params=None, **kwargs):
        return requests.get(self._full(url), params=params, **kwargs)

    @append_headers
    def post(self, url, data=None, json=None, **kwargs):
        return requests.post(self._full(url), data=data, json=json, verify=False, **kwargs)

    @append_headers
    def put(self, url, data=None, **kwargs):
        return requests.put(self._full(url), data=data, verify=False, **kwargs)

    @append_headers
    def delete(self, url, **kwargs):
        return requests.delete(self._full(url), **kwargs)


def append_auth(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        kwargs.update(auth=self.basic_auth)
        return func(self, *args, **kwargs)

    return wrapper


class BasicAuthRequest(Request):
    base_url = None
    basic_auth = HTTPBasicAuth(None, None)

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        if cls.base_url is None:
            raise ValueError
        return super_new(cls)

    def __init__(self):
        self.session = requests.Session()

    @append_auth
    def get(self, url, params=None, **kwargs):
        return self.session.get(self._full(url), params=params, verify=False, **kwargs)

    @append_auth
    def post(self, url, data=None, **kwargs):
        return self.session.post(self._full(url), data=data, verify=False, **kwargs)

    @append_auth
    def put(self, url, data=None, **kwargs):
        return self.session.put(self._full(url), data=data, verify=False, **kwargs)

    @append_auth
    def delete(self, url, **kwargs):
        return requests.delete(self._full(url), **kwargs)
