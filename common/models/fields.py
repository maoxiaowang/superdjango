import json

from IPy import IP, IPSet
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.core.validators import ListFieldValidator, DictFieldValidator, MACAddressValidator
from common.forms.fields import (
    DictField as FormDictField, ListField as FormListField,
    GenericObjectField as FormGenericObjectField)
from common.log import default_logger as logger
from common.utils.crypto import AESCrypt
from common.utils.json import is_json_str, CJsonEncoder

__all__ = [
    'JsonField',
    'DictField',
    'ListField',
    'GenericObjectField',
    'IPField',
    'IPSetField',
    'MACField',
    'MACSetField',
    'CryptoCharField',
]


class JsonField(models.TextField):
    max_length = 2048

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length') if 'max_length' in kwargs else self.max_length
        super().__init__(*args, max_length=max_length, **kwargs)

    def get_prep_value(self, value):
        # before saving to db, value could be a string or Promise
        if value is None:
            return value
        # call super method to internationalize value
        value = super().get_prep_value(value)
        # here, value could be a python object
        if isinstance(value, Exception):
            raise value
        return json.dumps(value, cls=CJsonEncoder)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, (dict, list)):
            return value
        else:
            if value is None:
                return
            try:
                return json.loads(value)
            except json.decoder.JSONDecodeError:
                return ValidationError(
                    self.error_messages['invalid'],
                    code='invalid',
                    params={'value': value}
                )

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return
        if is_json_str(value):
            return value
        return json.dumps(value, cls=CJsonEncoder)


class ListField(JsonField):
    description = _('List')
    default_error_messages = {
        'invalid': _('value must be a list-like jsonable string or null')
    }
    default_validators = [ListFieldValidator()]

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return
        if is_json_str(value):
            return value
        try:
            return json.dumps(value, cls=CJsonEncoder)
        except TypeError:
            return '[]'  # blank

    def to_python(self, value):
        if isinstance(value, str) and not value:
            return list()
        return super().to_python(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': FormListField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class DictField(JsonField):
    description = _('Dict')
    default_error_messages = {
        'invalid': _('value must be a dict-like jsonable string or null')
    }
    default_validators = [DictFieldValidator()]
    empty_values = {}

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return
        if is_json_str(value):
            return value
        try:
            return json.dumps(value, cls=CJsonEncoder)
        except TypeError:
            return '{}'  # blank

    def to_python(self, value):
        if isinstance(value, str) and not value:
            return dict()
        return super().to_python(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': FormDictField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class GenericObjectField(models.CharField):
    """
    根据字符串自动判断类型
    支持int，float，str，list，bool
    """
    max_length = 2048
    description = _('Generic object field')
    default_error_messages = {
        'type_error': _('Valid choices are int, float, str, list, bool.')
    }
    form_klass = FormGenericObjectField

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length') if 'max_length' in kwargs else self.max_length
        super().__init__(*args, max_length=max_length, **kwargs)

    # def value_to_string(self, obj):
    #     value = self.value_from_object(obj)
    #     if value is None:
    #         return
    #     return str(value)
    # 
    # def get_prep_value(self, value):
    #     return self.to_python(value)

    def from_db_value(self, value, expression, connection):
        return self.form_klass.typed_val(value)

    def to_python(self, value):
        value = super().to_python(value)
        return self.form_klass.raw_val(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': self.form_klass}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class IPField(models.CharField):
    max_length = 128
    description = _('IP field')
    default_error_messages = {
        'invalid': _('Value must a valid IPv4/IPv6 address (segment).')
    }

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length') if 'max_length' in kwargs else self.max_length
        super().__init__(*args, max_length=max_length, **kwargs)

    def get_prep_value(self, value):
        # before saving to db, value could be a string or Promise
        if value is None:
            return value
        # call super method to internationalize value
        value = super().get_prep_value(value)
        # here, value could be a python object
        return self.value_to_string(value)

    def value_to_string(self, obj):
        value = obj
        if isinstance(value, str):
            return
        else:
            # accept only IPSet object
            if isinstance(value, IP):
                return str(value)
            else:
                raise ValidationError('IPSet object excepted', code='error_ip')

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return
        if isinstance(value, IP):
            return value
        try:
            return IP(value)
        except (TypeError, ValueError):
            # invalid json data in db
            raise ValidationError(
                self.default_error_messages['invalid']
            )


class IPSetField(models.TextField):
    """
    python: IPSet([IP('192.168.1.1'), IP('::1'), IP('192.168.2.0/24')])
    str: (json) ["192.168.1.1", "::1", "192.168.2.0/24"]
    """
    max_length = 8192
    description = _('IP set field')
    default_error_messages = {
        'invalid': _('Value must a valid IPv4/IPv6 address or a segment.')
    }

    def get_prep_value(self, value):
        # before saving to db, value could be a string or Promise
        if value is None:
            return value
        # call super method to internationalize value
        value = super().get_prep_value(value)
        # here, value could be a python object
        return self.value_to_string(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, IPSet):
            return value
        try:
            ip_list = json.loads(value)
            ip_set = IPSet([IP(ip) for ip in ip_list])
            ip_set.optimize()
            return ip_set
        except (TypeError, json.decoder.JSONDecodeError):
            # invalid json data in db
            raise ValidationError(self.default_error_messages['invalid'])

    def value_to_string(self, obj):
        value = obj
        if isinstance(value, str):
            return
        else:
            # accept only IPSet object
            if isinstance(value, IPSet):
                return json.dumps(list(map(lambda x: str(x), value)))
            else:
                raise ValidationError('IPSet object excepted', code='error_ip')


class MACField(models.CharField):
    """
    XX:XX:XX:XX:XX:XX
    """
    max_length = 17
    description = _('MAC field')
    default_error_messages = {
        'invalid': _('Value must a valid IPv4/IPv6 address (segment).')
    }
    default_validators = [MACAddressValidator]

    def __init__(self, *args, **kwargs):
        max_length = kwargs.pop('max_length') if 'max_length' in kwargs else self.max_length
        super().__init__(*args, max_length=max_length, **kwargs)

    def get_prep_value(self, value):
        # before saving to db, value could be a string or Promise
        if value is None:
            return value
        # call super method to internationalize value
        value = super().get_prep_value(value)
        # here, value could be a python object
        value = self.value_to_string(value)
        value = value.replace('-', ':')
        return value

    def value_to_string(self, obj):
        if not isinstance(obj, str):
            return self.value_from_object(obj)
        return obj


class MACSetField(ListField):
    """
    这里只能保证新传入的MAC不重复，整个字段不重复需要在逻辑里处理下，如：
    s = list(set(s))
    s.sorted()
    """

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return
        if is_json_str(value):
            return value
        try:
            value = list(set(value))
            value.sort()
            return json.dumps(value)
        except TypeError:
            return '[]'  # blank


class CryptoCharField(models.CharField):
    """
    Type: aes, ...
    """
    CRYPT_AES = 'aes'
    valid_crypt_types = (CRYPT_AES,)
    default_crypt_type = CRYPT_AES
    default_error_messages = {
        'invalid': _('value must a valid encrypted string.')
    }

    def __init__(self, *args, crypt_type=None, crypt_key=None, **kwargs):
        if crypt_type:
            assert crypt_type in self.valid_crypt_types
            self.crypt_type = crypt_type
        else:
            self.crypt_type = self.default_crypt_type
        self.crypt_key = crypt_key or self._default_key
        self.crypt_object = self._get_crypt_object()
        super().__init__(*args, **kwargs)

    @property
    def _default_key(self):
        if self.crypt_type == self.CRYPT_AES:
            return '4141863181f34d80'

    def _get_crypt_object(self):
        if self.crypt_type == self.CRYPT_AES:
            return AESCrypt(self.crypt_key)

    def get_prep_value(self, value):
        """
        Converting simple text to encrypted value
        """
        if value is None:
            return value
        value = super().get_prep_value(value)
        if isinstance(value, Exception):
            raise value

        return self.value_to_string(value)

    def to_python(self, value):
        """
        Converting values to Python objects
        will be called in all circumstances when the data is loaded from the database
        """
        if value is None:
            return
        if isinstance(value, str) and not value:
            return value
        try:
            return self.crypt_object.decrypt(value)
        except Exception as e:
            # logger.error('Failed to decrypt (%s), %s' % (self.crypt_type, str(e)))
            # return exceptions.ValidationError(
            #     self.error_messages['invalid'],
            #     code='invalid',
            #     params={'value': value}
            # )
            return value

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj):
        """
        Converting field data for serialization
        """
        if obj is None:
            return
        if isinstance(obj, str):
            value = obj
        else:
            value = self.value_from_object(obj)
        try:
            return self.crypt_object.encrypt(value)
        except Exception as e:
            logger.error('Failed to encrypt (%s), %s' % (self.crypt_type, str(e)))
            return ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value}
            )


class CryptoFieldMixin:
    CRYPT_AES = 'aes'
    valid_crypt_types = (CRYPT_AES,)
    default_crypt_type = CRYPT_AES
    default_error_messages = {
        'invalid': _('value must a valid encrypted string.')
    }

    def __init__(self, *args, crypt_type=None, crypt_key=None, **kwargs):
        if crypt_type:
            assert crypt_type in self.valid_crypt_types
            self.crypt_type = crypt_type
        else:
            self.crypt_type = self.default_crypt_type
        self.crypt_key = crypt_key or self._default_key
        self.crypt_object = self._get_crypt_object()
        super().__init__(*args, **kwargs)

    @property
    def _default_key(self):
        if self.crypt_type == self.CRYPT_AES:
            return '4141863181f34d80'

    def _get_crypt_object(self):
        if self.crypt_type == self.CRYPT_AES:
            return AESCrypt(self.crypt_key)

    def get_prep_value(self, value):
        """
        Converting simple text to encrypted value
        """
        if value is None:
            return value
        value = super().get_prep_value(value)
        if isinstance(value, Exception):
            raise value

        return self.value_to_string(value)


class CryptoIntegerField(CryptoFieldMixin, models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 255
        super().__init__(*args, **kwargs)
        self.validators.append(validators.MaxLengthValidator(self.max_length))

    def get_prep_value(self, value):
        if value is None:
            return value
        value = super().get_prep_value(value)
        if isinstance(value, Exception):
            raise value
        return value

    def to_python(self, value):
        if value is None:
            return
        if isinstance(value, str) and not value:
            return value
        try:
            return int(self.crypt_object.decrypt(value))
        except Exception as e:
            return int(value)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj):
        if obj is None:
            return
        if isinstance(obj, int):
            value = int(obj)
        else:
            value = self.value_from_object(obj)
        try:
            crypt_value = self.crypt_object.encrypt(value)
            # setattr(crypt_value, self.attname, crypt_value)
            return crypt_value
        except Exception as e:
            logger.error('Failed to encrypt (%s), %s' % (self.crypt_type, str(e)))
            return ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value}
            )


class CryptoIPAddressField(CryptoFieldMixin, models.GenericIPAddressField):

    def get_prep_value(self, value):
        if value is None:
            return value
        value = super().get_prep_value(value)
        if isinstance(value, Exception):
            raise value
        return value

    def to_python(self, value):
        try:
            val = super().to_python(value)
            return self.crypt_object.decrypt(val)
        except Exception as e:
            return ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value}
            )

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def value_to_string(self, obj):
        if obj is None:
            return
        if isinstance(obj, str):
            value = obj
        else:
            value = self.value_from_object(obj)
        try:
            crypt_value = self.crypt_object.encrypt(value)
            # setattr(crypt_value, self.attname, crypt_value)
            return crypt_value
        except Exception as e:
            logger.error('Failed to encrypt (%s), %s' % (self.crypt_type, str(e)))
            return ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value}
            )
