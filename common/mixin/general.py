from datetime import datetime

from django.contrib.auth.mixins import PermissionRequiredMixin as _PermissionRequiredMixin
from django.db.models import Model
from django.http import QueryDict

from base.managers import OptLogManager
from common.core.exceptions import LoginRequired, MethodNotAllowed, PassVerificationError
from common.log import default_logger as logger

__all__ = [
    'LoginRequiredMixin',
    'PermissionRequiredMixin',
    'BaseViewMixin',
    'PasswordVerificationMixin'
]

from common.core.settings import sys_settings

from common.utils.crypto import AESCrypt


class PermissionRequiredMixin(_PermissionRequiredMixin):
    raise_exception = True


class LoginRequiredMixin:
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise LoginRequired
        return super().dispatch(request, *args, **kwargs)


class BaseViewMixin:
    # API related
    is_api: bool = True
    author: str = None
    updated_at: datetime = None

    def dispatch(self, request, *args, **kwargs):
        # set operation logger
        self.opt_logger = OptLogManager(request)
        return super().dispatch(request, *args, **kwargs)

    def opt_log(self) -> Model:
        """
        As for create view, self.object is now at the time
        """
        pass

    def http_method_not_allowed(self, request, *args, **kwargs):
        raise MethodNotAllowed


class PasswordVerificationMixin:
    """The password for verification."""

    def dispatch(self, request, *args, **kwargs):
        param = QueryDict(request.body)
        password = param.get("password")
        password = password or request.GET.get("password")
        try:
            password = AESCrypt(sys_settings.default.aes_key).decrypt(password)
        except Exception as e:
            if sys_settings.default.debug:
                logger.warning("密码解密失败，以密文继续登录", e)
                pass
            else:
                raise PassVerificationError
        user = request.user
        rest = user.check_password(password)
        # if not rest:
            # raise PassVerificationError
        return super().dispatch(request, *args, **kwargs)