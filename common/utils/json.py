import decimal
import json
import uuid
from datetime import datetime, date, time

import IPy
import bson
from django.db.models.fields.files import FieldFile
from django.utils import timezone
from django.utils.functional import Promise
from django.forms import model_to_dict
from django.db.models import Model
from django.utils.timezone import get_current_timezone

from common.constants import SENSITIVE_FIELDS

__all__ = [
    'CJsonEncoder',
    'is_json_str',
]


class CJsonEncoder(json.JSONEncoder):
    objects_to_string = (bson.ObjectId, decimal.Decimal, uuid.UUID, Promise, IPy.IP)

    def default(self, obj):
        if isinstance(obj, datetime):
            return timezone.localtime(obj).strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            obj = datetime(obj.year, obj.month, obj.day, 0, 0, 0, tzinfo=get_current_timezone())
            return timezone.localdate(obj).strftime('%Y-%m-%d')
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, self.objects_to_string):
            return str(obj)
        elif isinstance(obj, IPy.IPSet):
            return list(map(lambda x: str(x), obj))
        elif obj.__class__.__name__ == 'GenericRelatedObjectManager':
            return
        elif isinstance(obj, FieldFile):
            if obj:
                return obj.url
        elif isinstance(obj, Model):
            return model_to_dict(obj, exclude=SENSITIVE_FIELDS)
        else:
            return json.JSONEncoder.default(self, obj)


def is_json_str(raw_str):
    if isinstance(raw_str, str):
        try:
            json.loads(raw_str)
        except ValueError:
            return False
        return True
    else:
        return False
