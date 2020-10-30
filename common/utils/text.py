"""
String helper
"""
import hashlib
import json
import re
import sys
import typing
import uuid

__all__ = [
    'is_int', 'is_float', 'is_list', 'is_dict', 'is_tuple', 'is_bool',
    'str_len', 'str2int', 'str2float', 'str2digit', 'str2bool',
    'str2base', 'str2iter',
    'obj2iter', 'UUID', 'md5_encode', 'get_filename_extension'
]

# Notice: Following regex patterns are not accurate, may cause unexpected errors
REGEX_INT = r'^-?\d+$'
REGEX_FLOAT = r'^-?\d+\.\d+$'
REGEX_LIST = r'^\[.*?\]$'
REGEX_DICT = r'^\{.*?}\}$'
REGEX_TUPLE = r'^(\(.*?\)|\(\))$'
REGEX_BOOL = r'^(true|false)'


def is_int(obj):
    if isinstance(obj, str):
        return bool(re.match(REGEX_INT, obj))
    elif isinstance(obj, int):
        return True
    return False


def is_float(obj: typing.Union[float, str]):
    if isinstance(obj, str):
        return bool(re.match(REGEX_FLOAT, obj))
    elif isinstance(obj, float):
        return True
    return False


def is_list(obj: typing.Union[list, str], json_required=True):
    if isinstance(obj, str) and re.match(REGEX_LIST, obj):
        if json_required:
            try:
                json.loads(obj)
            except json.JSONDecodeError:
                return False
        return True
    elif isinstance(obj, list):
        return True
    return False


def is_dict(obj, json_required=True):
    if isinstance(obj, str) and re.match(REGEX_DICT, obj):
        if json_required:
            try:
                json.loads(obj)
            except json.JSONDecodeError:
                return False
        return True
    elif isinstance(obj, dict):
        return True
    return False


def is_tuple(obj):
    if isinstance(obj, tuple):
        return True
    elif isinstance(obj, str) and re.match(REGEX_TUPLE, obj):
        return True
    return False


def is_bool(string, strict=True):
    flags = 0
    if not strict:
        flags = re.IGNORECASE
    return bool(re.match(REGEX_BOOL, string, flags=flags))


def str_len(string):
    """
    Chinese characters or other non-ascii chars
    will be traded as two ascii chars
    """
    length = None
    encoding = sys.getdefaultencoding()
    if encoding == 'utf-8':
        # Linux liked system
        length = len(string.encode('gbk'))
    else:
        # TODO: when system encoding is not utf-8
        pass
    return length


def str2int(string, default=None, silent=False):
    """Raise exceptions if default is None"""
    if isinstance(string, int):
        return string
    elif isinstance(string, str):
        if is_int(string):
            return int(string)
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2float(string, default=None, silent=False) -> float:
    """Raise exceptions if default is None"""
    if isinstance(string, float):
        return string
    elif isinstance(string, str):
        if re.match(r'^-?\d+\.?\d*$', string):
            return float(string)
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2digit(string, default=None):
    """
    String to int or float
    """
    if isinstance(string, (int, float)):
        return string
    elif isinstance(string, str):
        if is_int(string):
            return str2int(string, default=default)
        elif re.match(REGEX_FLOAT, string):
            return str2float(string, default=default)


def str2bool(string, default: bool = None, silent=False):
    """
    str to bool
    """
    if isinstance(string, bool):
        return string
    elif isinstance(string, str):
        if string in ('true', 'True'):
            return True
        elif string in ('false', 'False'):
            return False
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2base(string):
    """
    Turn string to Base type (int, float, bool or str),
    not including list, dict ...
    """
    if not isinstance(string, str):
        return string
    if is_int(string):
        return int(string)
    elif is_float(string):
        return float(string)
    elif string in ('true', 'True'):
        return True
    elif string in ('false', 'False'):
        return False
    else:
        return string


def str2iter(string):
    """
    Turn string to list, tuple, set or str
    """
    if not isinstance(string, str):
        return string
    if is_list(string):
        return eval(string)
    elif is_dict(string):
        return eval(string)
    elif is_dict(string):
        return eval(string)
    else:
        return string


def obj2iter(obj):
    """
    Simply translate an common object to an iterable object.
    Non-iterable object will be turned to a list.
    """
    return obj if isinstance(obj, (list, tuple, dict)) else [obj]


class UUID(object):

    @property
    def uuid4(self):
        return str(uuid.uuid4())

    @property
    def uuid4_without_line(self):
        return str(uuid.uuid4()).replace('-', '')

    @property
    def uuid4_underline(self):
        return str(uuid.uuid4()).replace('-', '_')


UUID = UUID()


def md5_encode(string):
    """
    Hash a string with MD5
    """
    assert isinstance(string, str)
    m2 = hashlib.md5()
    m2.update(string.encode())
    return m2.hexdigest()


def get_filename_extension(filename):
    res = re.findall(r'^.*\.(.*)$', filename)
    extension = res[0] if res else None
    return extension
