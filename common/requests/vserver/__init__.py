import json

import xmltodict

from common.requests import BasicAuthRequest


class VServerRequest(BasicAuthRequest):

    def get(self, url, params=None, **kwargs):
        res = super().get(url, params=params, **kwargs)
        o = xmltodict.parse(res.content)
        return json.loads(json.dumps(o))

    def post(self, url, data=None, **kwargs):
        res = super().post(url, data=data, **kwargs)
        o = xmltodict.parse(res.content)
        return json.loads(json.dumps(o))
