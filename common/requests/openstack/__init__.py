import datetime
import json

import requests
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _

from common.core.exceptions import ECloudException
from common.core.settings import sys_settings
from common.requests import TokenRequest, Token, TokenExpiresAt
from common.utils.datetime import str_to_datetime


class OpenStackError(ECloudException):
    desc = _('OpenStack Error')


class OpenStackToken(Token):
    key = '_openstack_token'
    expires_at = TokenExpiresAt(key='_openstack_token_expires')
    
    def get_token_and_expired_at(self) -> (str, datetime.datetime):
        data = {
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "name": sys_settings.openstack.username,
                            "domain": {
                                "name": sys_settings.openstack.domain_name
                            },
                            "password": sys_settings.openstack.password
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {
                            "id": sys_settings.openstack.domain_id
                        },
                        "name": sys_settings.openstack.username
                    }
                }
            }
        }
        response = requests.post(
            sys_settings.openstack.auth_url,
            json=data,
            headers={
                'Content-Type': 'application/json',
            }
        )
        if response.status_code != 201:
            raise Exception(response.text)
        content = json.loads(response.content)
        token = response.headers.get('X-Subject-Token')
        expires_at = str_to_datetime(content['token']['expires_at'])
        return token, expires_at


class OpenStackRequest(TokenRequest):
    token_field_name = 'X-Auth-Token'
    token = OpenStackToken()
    error_name = 'OpenStack Error'
    default_error_class = OpenStackError
    sub_name = None

    def _get_token(self):
        return self.token

    def _handle_response(self, response):
        key = list(response.keys())[0]
        if key == self.error_name:
            # occur some errors
            raise self.default_error_class(response[self.error_name]['message'])
        # may be successful
        return response[key]

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs).json()
        return self._handle_response(response)

    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs).json()
        return self._handle_response(response)

    def put(self, *args, **kwargs):
        response = super().put(*args, **kwargs).json()
        return self._handle_response(response)

    def delete(self, *args, **kwargs):
        response = super().delete(*args, **kwargs)
        if response.content:
            return self._handle_response(response)
        return
