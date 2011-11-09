# coding: utf-8
import random
import time
import urllib
import warnings
from hashlib import md5
from functools import partial
try:
    import json
except ImportError:
    import simplejson as json
from vkontakte import http

API_URL = 'http://api.vk.com/api.php'
DEFAULT_TIMEOUT = 1

class VKError(Exception):
    __slots__ = ["code", "description", "params"]
    def __init__(self, code, description, params):
        self.code, self.description, self.params = (code, description, params)
        Exception.__init__(self, str(self))
    def __str__(self):
        return "Error(code = '%s', description = '%s', params = '%s')" % (self.code, self.description, self.params)

def _to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf8')
    return s # this can be number, etc.

def signature(api_secret, params):
    keys = sorted(params.keys())
    param_str = "".join(["%s=%s" % (str(key), _to_utf8(params[key])) for key in keys])
    return md5(param_str+str(api_secret)).hexdigest()

def _sig(api_secret, **kwargs):
    msg = 'vkontakte.api._sig is deprecated and will be removed. Please use `vkontakte.signature`'
    warnings.warn(msg, DeprecationWarning, stacklevel=2)
    return signature(api_secret, kwargs)


def request(api_id, api_secret, method, timestamp=None, timeout=DEFAULT_TIMEOUT, **kwargs):
    params = dict(
        api_id = str(api_id),
        method = method,
        format = 'JSON',
        v = '3.0',
        random = random.randint(0, 2**30),
        timestamp = timestamp or int(time.time())
    )
    params.update(kwargs)
    params['sig'] = signature(api_secret, params)
    data = urllib.urlencode(params)

    # urllib2 doesn't support timeouts for python 2.5 so
    # custom function is used for making http requests
    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    return http.post(API_URL, data, headers, timeout)


class API(object):
    def __init__(self, api_id, api_secret, **defaults):
        self.api_id = api_id
        self.api_secret = api_secret
        self.defaults = defaults
        self.method_prefix = ''

    def get(self, method, timeout=DEFAULT_TIMEOUT, **kwargs):
        status, response = request(self.api_id, self.api_secret, method, timeout = timeout, **kwargs)
        if not (status >= 200 and status <= 299):
            raise VKError(status, "HTTP error", kwargs)

        data = json.loads(response)
        if "error" in data:
            raise VKError(data["error"]["error_code"], data["error"]["error_msg"], data["error"]["request_params"])
        return data['response']

    def __getattr__(self, name):

        # support for api.secure.<methodName> syntax
        if (name=='secure'):
            api = API(self.api_id, self.api_secret, **self.defaults)
            api.method_prefix = 'secure.'
            return api

        # the magic to convert instance attributes into method names
        return partial(self, method=name)

    def __call__(self, **kwargs):
        method = kwargs.pop('method')
        params = self.defaults.copy()
        params.update(kwargs)
        return self.get(self.method_prefix + method, **params)

