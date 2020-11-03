from django.http import QueryDict

from base.exceptions import PasswordValidationError


class PasswordVerificationMixin:
    """password verification"""

    def dispatch(self, request, *args, **kwargs):
        param = QueryDict(request.body)
        password = param.get("password")
        password = password or request.GET.get("password")

        user = request.user
        if not user.check_password(password):
            raise PasswordValidationError
        return super().dispatch(request, *args, **kwargs)