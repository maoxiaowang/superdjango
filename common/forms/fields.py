import json

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from common.core.validators import ListFieldValidator, DictFieldValidator
from common.utils.text import str2bool, is_list, is_float, is_int

__all__ = [
    'JsonField',
    'ListField',
    'DictField',
    'GenericObjectField'
]


class JsonField(forms.CharField):
    default_error_messages = {
        'invalid_json': _('Value %(value)s is not a jsonable string.')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'],
                code='required',
                params={'value': value}
            )

        if value in self.empty_values:  # empty_values和blank有关
            return value
        # if isinstance(value, (dict, list)):
        #     return value
        else:
            if value is None:
                return
            try:
                # 解决多form中数据多次转换问题
                if type(value) == list:
                    return value
                return json.loads(value)
            except json.decoder.JSONDecodeError as e:
                raise ValidationError(
                    self.error_messages['invalid_json'],
                    code='invalid_json',
                    params={'value': value}
                )


class ListField(JsonField):
    description = _("list")

    def get_internal_type(self):
        return "ListField"

    default_error_messages = {
        'invalid_json': _("Value '%(value)s' is not a list-like string or null.")
    }
    default_validators = [ListFieldValidator()]


class DictField(JsonField):
    description = _("dict")

    def get_internal_type(self):
        return "DictField"

    default_error_messages = {
        'invalid_json': _('Value %(value)s is not a dict-like string or null.')
    }
    default_validators = [DictFieldValidator()]


class GenericObjectField(forms.CharField):
    description = 'Generic object field'

    @staticmethod
    def typed_val(val):
        """
        将字符串转为对应类型对象
        根据特征明显程度：list -> float, int -> bool -> str
        """
        if val is None:
            return
        b = str2bool(val, silent=True)
        if is_list(val):
            return json.loads(val)
        elif is_float(val):
            return float(val)
        elif is_int(val):
            return int(val)
        elif b is not None:
            return b
        elif isinstance(val, str):
            return val
        raise forms.ValidationError(
            _('Type error, choices are int, float, str, list, bool or None.')
        )

    @staticmethod
    def raw_val(val):
        if val is None:
            return
        if isinstance(val, (list, dict)):
            return json.dumps(val)
        return str(val)

    def to_python(self, value):
        value = self.typed_val(value)
        return super().to_python(value)
