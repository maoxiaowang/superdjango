"""
Exceptions codes:

Exceptions level:
error, warning, info

Exceptions desc:
short and accurate description for an exception


"""
import json

from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _


class SException(Exception):
    """
    Base exception
    """
    level = 'error'
    desc = _('Undefined exceptions')
    code = 500

    def __init__(self, msg=None, **kwargs):
        self.msg = msg or ''
        self.kwargs = kwargs

    def __str__(self):
        if self.msg:
            if self.desc is None or not self.desc.strip():
                res = format_lazy('{}', str(self.msg))
            else:
                res = format_lazy('{}，{}', self.desc, str(self.msg))
        else:
            res = self.desc
        return str(res)


# System common exceptions
# 601 - 999

class InvalidParameter(SException):
    """
    Invalid parameter from request
    If both `param` and `msg` were passed in, `param` will be used.
    """
    desc = _('Invalid parameter')
    code = 401

    def __init__(self, msg=None, param=None, **kwargs):
        self.param = param
        self.msg = '' if msg is None else msg
        super().__init__(msg, **kwargs)

    def __str__(self):
        if self.param:
            self.msg = _('%(item)s is not valid.' % {'item': self.param})
        return super().__str__()


class ValidationError(SException):
    """
    Used in forms, similar to InvalidParameter
    """

    desc = _('Validation error')
    code = 402


class PermissionDenied(SException):
    desc = _('Permission denied')
    level = 'warning'
    code = 403


class MethodNotAllowed(SException):
    """
    Method of http request is not allowed
    """
    desc = _('Method not allowed')
    code = 405


class LoginRequired(SException):
    """
    "Login required
    """

    desc = _('Login required')
    code = 406


class ObjectAlreadyExist(SException):
    """
    For create or add actions
    """

    desc = _('Object already exist')
    code = 407


class EmptyObjectNotAllowed(SException):
    """
    Empty object is not allowed
    """

    desc = _('Empty object not allowed')
    code = 408


class OperationNotAllowed(SException):
    """
    Operation is not allowed

    This is different from 403 permission denied
    """
    desc = _('Operation not allowed')
    code = 409


class OperationFailed(SException):
    """
    Failed to do operations, e.g. create, update, delete
    """
    desc = _('Operation failed')
    code = 410
