from django.contrib.auth.mixins import PermissionRequiredMixin as _PermissionRequiredMixin
from django.http import QueryDict

from common.core.exceptions import LoginRequired, MethodNotAllowed

__all__ = [
    'LoginRequiredMixin',
    'PermissionRequiredMixin',
    'BaseViewMixin',
]


class PermissionRequiredMixin(_PermissionRequiredMixin):
    raise_exception = True


class LoginRequiredMixin:
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise LoginRequired
        return super().dispatch(request, *args, **kwargs)


class BaseViewMixin:

    async def __call__(self, *args, **kwargs):
        await super().__call__()

    def http_method_not_allowed(self, request, *args, **kwargs):
        raise MethodNotAllowed
