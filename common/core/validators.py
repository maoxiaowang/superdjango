import json
import re

from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _


@deconstructible
class ListFieldValidator(validators.RegexValidator):
    regex = r'^(\[.*?\]|null)$'
    message = _(
        'List field only accepts list-like or null string'
    )
    flags = re.UNICODE


@deconstructible
class DictFieldValidator(validators.RegexValidator):
    regex = r'^(\{.*?\}|null)$'
    message = _(
        'Enter a valid username. This value may contain only English letters, '
        'numbers, and @/./+/-/_ characters.'
    )
    flags = re.UNICODE


@deconstructible
class MACAddressValidator(validators.RegexValidator):
    """
    Validate that form of the string is a MAC address.
    """
    message = _('MAC address must be like "08:00:20:0A:8C:6D" or "08-00-20-0A-8C-6D".')
    code = 'invalid_mac_address'
    regex = r'^(([0-9a-f]{2}:){5}[0-9a-f]{2}|([0-9a-f]{2}-){5}[0-9a-f]{2})$'
    flags = re.ASCII


@deconstructible
class SimpleNameValidator(validators.RegexValidator):
    message = '名称只能包含字母、数字、中划线、下划线。'
    code = 'invalid_name'
    regex = r'^[\w\d\-]+$'
    flags = re.ASCII


@deconstructible
class ChineseNameValidator(validators.RegexValidator):
    message = '名称只能包含字母、数字、中划线、下划线和中文。'
    code = 'invalid_name'
    regex = r'^[\w\d\-\u4e00-\u9fa5]+$'
    flags = re.UNICODE


@deconstructible
class DotChineseNameValidator(validators.RegexValidator):
    message = '名称只能包含字母、数字、中划线、下划线、英文点号和中文。'
    code = 'invalid_name'
    regex = r'^[.\w\d\-\u4e00-\u9fa5]+$'
    flags = re.UNICODE


@deconstructible
class SymbolChineseNameValidator(validators.RegexValidator):
    message = '名称只能包含字母、数字、中文以及特殊符号~!@#$%&*()._-。'
    code = 'invalid_name'
    regex = r'^[\~\.\-\!\@\#\$\%\&\*\(\)\w\d\u4e00-\u9fa5]+$'
    flags = re.UNICODE


@deconstructible
class IntListValidator:
    messages = {
        'invalid': _("Value '%(value)s' is not a list-like string or null."),
        'invalid_element': _("Non-integer element '%(element)s' is not allowed."),
        'out_of_scope': _("Negative value '%(element)s' is not allowed.")
    }

    def __init__(self, seq=',', allow_negative=False):
        self.allow_negative = allow_negative
        self.seq = seq

    def __call__(self, value):
        cleaned = self.clean(value)
        for el in cleaned:
            if not isinstance(el, int):
                raise ValidationError(
                    self.messages['invalid_element'],
                    params={'element': el},
                    code='invalid_element'
                )
            if not self.allow_negative and el < 0:
                raise ValidationError(
                    self.messages['out_of_scope'],
                    params={'element', el},
                    code='out_of_scope'
                )

    def clean(self, x):
        if isinstance(x, str):
            try:
                x = json.loads(x)
            except json.JSONDecodeError:
                raise ValidationError(
                    self.messages['invalid'], code='invalid', params={'value': x}
                )
        return x
