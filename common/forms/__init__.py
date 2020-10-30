import json
import typing
import uuid
from itertools import chain

from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import Model, QuerySet
from django.forms.utils import ErrorDict, ErrorList
from django.utils import timezone, dateparse
from django.utils.translation import gettext
from pytz import utc

import common.models.fields as model_fields
from common.constants import SENSITIVE_FIELDS
from common.utils.json import CJsonEncoder
from common.forms.forms import *


def form_errors_to_list(errors):
    assert isinstance(errors, ErrorDict)
    return [item[0]['message'] for item in list(json.loads(errors.as_json()).values())]


class DivErrorList(ErrorList):

    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''

        return \
            ('<div class="%s">%s</div>' %
             (self.error_class,
              ''.join(
                  ['<div class="alert alert-danger alert-dismissible fade show">'
                   '<button type="button" class="close" data-dismiss="alert">×</button>'
                   '%s</div>' % e for e in self]))
             )

    def as_list(self):
        output = []
        for field, errors in self.items():
            output.append('%s' % e for e in errors)
        return output


def model_to_dict(instance, fields=None, exclude=None, many_to_many=False,
                  i18n_fields=None,
                  related_sets: tuple = None,
                  many_to_many_fields: tuple = None,
                  **kwargs):
    """
    Return a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.

    ``related_sets`` is an optional list of reversed many-to-many field names

    ``many_to_many_fields`` is an optional list of many-to-many field names,
    used to show m2m data
    """
    if instance is None:
        return
    use_natural_foreign_keys = kwargs.get('use_natural_foreign_keys', False)
    opts = instance._meta
    data = {}
    default_exclude = SENSITIVE_FIELDS
    if exclude:
        exclude = [exclude] if isinstance(exclude, str) else list(exclude)
        exclude.extend(default_exclude)
        exclude = list(set(exclude))
    else:
        exclude = default_exclude
    chains = chain(opts.concrete_fields, opts.private_fields)
    if many_to_many and many_to_many_fields:
        chains = chain(chains, opts.many_to_many)

    for f in chains:
        # if not getattr(f, 'editable', False):
        #     continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, GenericForeignKey):
            value = getattr(instance, f.name)
            value = model_to_dict(value)
        else:
            value = f.value_from_object(instance)
        if isinstance(f, models.DateTimeField):
            if value is None:
                continue
            if isinstance(value, str):
                naive = dateparse.parse_datetime(value)
                aware = utc.localize(naive, is_dst=None)
            else:
                aware = timezone.localtime(value)
            value = aware.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(f, models.DateField):
            if value is None:
                continue
            if isinstance(value, str):
                naive = dateparse.parse_date(value)
                aware = utc.localize(naive, is_dst=None)
            else:
                aware = timezone.localdate(value)
            value = aware.strftime('%Y-%m-%d')
        elif isinstance(f, models.ForeignKey) and use_natural_foreign_keys:
            if hasattr(f.related_model, 'natural_key') and callable(getattr(f.related_model, 'natural_key')):
                fk = getattr(instance, f.name)
                value = f.related_model.natural_key(fk) if fk else fk

            # if not many_to_many_fields or many_to_many_fields and f.name in many_to_many_fields:
            #     # only serialize fields in many_to_many_fields or many_to_many_fields is empty
            #     if hasattr(f.model, 'natural_key') and callable(getattr(f.model, 'natural_key')):
            #         value = instance._meta.model.natural_key(instance)
        else:
            # i18n
            if i18n_fields:
                assert isinstance(i18n_fields, (list, tuple, str))
                i18n_fields = [i18n_fields] if isinstance(i18n_fields,
                                                          str) else i18n_fields
                if f.name in i18n_fields:
                    value = gettext(value)
        data[f.name] = value

    if related_sets:
        for rs in related_sets:
            if not hasattr(instance, rs):
                # try:
                #     getattr(instance, rs)
                # except Exception as e:
                #     if e.__class__.__name__ == 'RelatedObjectDoesNotExist':
                #         data[rs] = None
                #         continue
                raise AttributeError(
                    "'%s' is not a valid attribute for model '%s'." %
                    (rs, instance._meta.model_name)
                )
            item_set = getattr(instance, rs)
            if not item_set.__class__.__name__.endswith('RelatedManager'):
                raise AttributeError(
                    "'%s' is not a valid value for 'related_sets', "
                    "may be you need 'many_to_many_fields'?" % rs
                )
            data[rs] = queryset_to_list(item_set.all())
    if many_to_many_fields:
        for m2m in many_to_many_fields:
            if not hasattr(instance, m2m):
                try:
                    # 一对一反向
                    getattr(instance, m2m)
                except Exception as e:
                    if e.__class__.__name__ == 'RelatedObjectDoesNotExist':
                        data[m2m] = None
                        continue
                raise AttributeError(
                    "'%s' is not a valid attribute for model '%s'." %
                    (m2m, instance._meta.model_name)
                )
            m2m_obj = getattr(instance, m2m)
            if m2m_obj is not None and not isinstance(m2m_obj, Model):
                raise AttributeError(
                    "'%s' is not a valid value for 'many_to_many_fields', "
                    "may be you need 'related_sets'?" % m2m
                )
            data[m2m] = model_to_dict(m2m_obj)
    data = json.dumps(data, cls=CJsonEncoder)
    data = json.loads(data)
    return data


def queryset_to_list(queryset, fields=None, exclude=None, many_to_many=False,
                     i18n_fields=None, **kwargs):
    data = list()
    for item in queryset:
        if isinstance(item, Model):
            data.append(
                model_to_dict(
                    item, fields=fields, exclude=exclude,
                    many_to_many=many_to_many,
                    i18n_fields=i18n_fields, **kwargs
                )
            )
        else:
            data.append(item)
    return data


class Serializer(object):

    def __init__(self, queryset: typing.Union[QuerySet, Model, list], fields=None, exclude=None,
                 related_sets=None, many_to_many_fields=None, **kwargs):
        """
        Notice: queryset is a QuerySet or an instance of a model

        kwargs:
        use_natural_foreign_keys
        use_natural_primary_keys

        related_sets: reversed models
        many_to_many_fields: foreign key or one to one
        """
        if not queryset:
            self.sj = list()
            return

        # turn model instance to object list
        is_queryset = True
        default_exclude = SENSITIVE_FIELDS
        if isinstance(queryset, QuerySet):
            pk_name = queryset.model._meta.pk.attname
        else:
            is_queryset = False
            if isinstance(queryset, Model):
                pk_name = queryset._meta.pk.attname
                queryset = [queryset]

        # construct and serialize
        if exclude:
            exclude = [exclude] if isinstance(exclude, str) else list(exclude)
            default_exclude.extend(exclude)
        serialized = queryset_to_list(
            queryset, many_to_many=True,
            many_to_many_fields=many_to_many_fields,
            related_sets=related_sets,
            fields=fields,
            exclude=default_exclude, **kwargs)

        # return directly for annotate operations
        if hasattr(queryset[0], '_meta'):
            self.sj = serialized
            return

        special_fields = set()
        crypto_fields = set()
        for qs in queryset:
            for f in qs._meta.fields:
                if isinstance(f, (model_fields.DictField, model_fields.ListField)):
                    special_fields.add(f.name)
                elif isinstance(f, model_fields.CryptoCharField):
                    crypto_fields.add(f.name)

        # serialized = json.loads(sj)

        # exclude fields
        # for item in serialized:
        #     print(item)
        #     print(type(item))
        #     fields = item['fields']
        #     fields_copy = copy.deepcopy(fields)
        #     for k, v in fields_copy.items():
        #         if k in default_exclude:
        #             del fields[k]
        for i, item in enumerate(serialized):
            item['pk'] = queryset[i].pk

        # get related-data in related_sets
        # 反向查询
        if related_sets:
            for rs in related_sets:
                if not hasattr(queryset.model, rs):
                    raise AttributeError(rs)
                # reversed one to one
                if (hasattr(getattr(queryset.model, rs), 'related') and
                        getattr(getattr(queryset.model, rs), 'related').one_to_one):
                    for item in queryset:
                        if hasattr(item, rs):
                            item_set = getattr(item, rs)
                            for s in serialized:
                                if isinstance(item.pk, uuid.UUID):
                                    item.pk = str(item.pk)
                                if s['pk'] == item.pk:
                                    s[rs] = model_to_dict(item_set)
                                    break
                        else:
                            for s in serialized:
                                if s['pk'] == item.pk:
                                    s[rs] = None
                                    break
                else:
                    for item in queryset:
                        item_set = getattr(item, rs)
                        qs = item_set.all()
                        for s in serialized:
                            if s['pk'] == item.pk:
                                s[rs] = queryset_to_list(qs)
                                break
        # 正向查询
        if many_to_many_fields:
            for m2m in many_to_many_fields:
                if not hasattr(queryset.model, m2m):
                    raise AttributeError(m2m)
                # many to many
                if getattr(getattr(queryset.model, m2m), 'field').many_to_many:
                    for item in queryset:
                        qs = getattr(item, m2m).all()
                        for s in serialized:
                            if s['pk'] == item.pk:
                                s[m2m] = queryset_to_list(qs)
                                break
                # many to one / one to one
                elif (getattr(getattr(queryset.model, m2m), 'field').many_to_one or
                      getattr(getattr(queryset.model, m2m), 'field').one_to_one):
                    for item in queryset:
                        qs = getattr(item, m2m)
                        for s in serialized:
                            if s['pk'] == item.pk:
                                if qs:
                                    s[m2m] = model_to_dict(qs)
                                    break
                                else:
                                    s[m2m] = None
                                    break

        # add pk to fields, deal with other fields
        for i, item in enumerate(serialized):
            item[pk_name] = item['pk']
            item['pk'] = item['pk']
            for f in item:
                if f in special_fields:
                    if item[f] is None:
                        continue
                    # item[f] = json.loads(item[f])
                elif f in crypto_fields:
                    item[f] = getattr(queryset[i], f)

        # if fields_only:
        #     serialized = [item['fields'] for item in serialized]
        #     if exclude:
        #         if isinstance(exclude, str):
        #             exclude = [exclude]
        #         for s in serialized:
        #             for e in exclude:
        #                 if e in s:
        #                     s.pop(e)

        self.sj = serialized if is_queryset else serialized[0]

    def to_json(self):
        return json.dumps(self.sj)

    def to_python(self):
        return self.sj
