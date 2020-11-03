import datetime
import typing
from itertools import chain

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db import models
from django.db.models.query import QuerySet
from django.http.request import QueryDict
from django.http.response import (
    Http404
)
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    ListView as _ListView, DetailView as _DetailView, DeleteView as _DeleteView,
    CreateView as _CreateView, UpdateView as _UpdateView, View as _View,
    FormView as _FormView, TemplateView as _TemplateView)

from base.managers import OptLogManager
from common.core.db import MongoDB
from common.core.exceptions import InvalidParameter
from common.forms import queryset_to_list
from common.mixin import ResponseMixin, FormValidationMixin
from common.mixin.general import BaseViewMixin
from common.paginator import MongoPaginator
from common.utils.datetime import to_aware_datetime
from common.utils.text import str2iter, str2bool, str2int, str2float

__all__ = [
    'View', 'FormView', 'TemplateView', 'NoModelListView', 'AdvancedListView', 'BulkDeleteView',
    'ListView', 'CreateView', 'DetailView', 'UpdateView', 'DeleteView'
]


class View(BaseViewMixin, ResponseMixin, _View):

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response


class FormView(BaseViewMixin, FormValidationMixin, ResponseMixin, _FormView):
    http_method_names = ['post']

    def put(self, *args, **kwargs):
        self.request.POST = QueryDict(self.request.body)
        return super().put(*args, **kwargs)


class TemplateView(BaseViewMixin, _TemplateView):
    """
    Notice: Inherit LoginRequiredMixin by yourself for this view
    """
    pass


class ListView(ResponseMixin, BaseViewMixin, _ListView):
    http_method_names = ['get']

    def get_object_list(self, **kwargs):
        queryset = self.get_queryset()
        return queryset

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_object_list(**kwargs)
        return self.render_to_json_response(data=self.object_list)


class NoModelListView(ListView):
    paginator_class = Paginator  # 默认MySQL分页
    page_kwarg = 'page'
    # 要显示的外键的反查询集，在这里填对应model的名字（全小写）。
    related_sets: tuple = None
    # 要显示的正向一对多/多对多的查询集
    many_to_many_fields: tuple = None
    collection = None
    show_all = False
    total_length = None

    def __init__(self):
        self.object_list = None
        super().__init__()

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        cls.check_attr()
        return super_new(cls)

    @classmethod
    def check_attr(cls):
        if cls.related_sets and not isinstance(cls.related_sets, tuple):
            raise AttributeError('\'related_sets\' must be a tuple.')
        if cls.many_to_many_fields and not isinstance(cls.many_to_many_fields, tuple):
            raise AttributeError('\'many_to_many_fields\' must be a tuple.')

    def get_object_list(self, **kwargs):
        """
        Paginate the queryset and return paged list of items
        """
        # filter & order
        queryset = super().get_object_list(**kwargs)
        # queryset = self.get_queryset()

        self.total_length = len(queryset)

        # pagination
        page_size = self.get_page_size()
        if page_size and not self.get_show_all():
            try:
                paginator, page, self.object_list, has_another_page = self.paginate_queryset(
                    queryset, page_size)
            except Http404:
                # this is for frontend pagination
                return list()
            self.paginator = paginator
            self.page = page
        else:
            self.object_list = queryset
        if self.paginator_class is MongoPaginator:
            # make collection result to list
            self.object_list = list(self.object_list)
        return self.object_list

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.request.GET.get('orderBy') or self.ordering

    def get_page_size(self):
        return str2int(self.request.GET.get('pageSize'), default=10)

    def get_show_all(self):
        self.show_all = str2bool(self.request.GET.get('all', False))
        return self.show_all

    def get_queryset(self):
        queryset = []
        return queryset


class AdvancedListView(ListView):
    paginator_class = Paginator  # 默认MySQL分页
    page_kwarg = 'page'
    # 要显示的外键的反查询集，在这里填对应model的名字（全小写）。
    related_sets: tuple = None
    # 要显示的正向一对多/多对多的查询集
    many_to_many_fields: tuple = None
    collection = None
    show_all = False
    total_length = None

    def __init__(self):
        self.object_list = None
        super().__init__()

    def __new__(cls, *args, **kwargs):
        super_new = super().__new__
        cls.check_attr()
        return super_new(cls)

    @classmethod
    def check_attr(cls):
        if cls.related_sets and not isinstance(cls.related_sets, tuple):
            raise AttributeError('\'related_sets\' must be a tuple.')
        if cls.many_to_many_fields and not isinstance(cls.many_to_many_fields, tuple):
            raise AttributeError('\'many_to_many_fields\' must be a tuple.')

    def get_object_list(self, **kwargs):
        """
        Paginate the queryset and return paged list of items
        """
        # filter & order
        queryset = super().get_object_list(**kwargs)
        queryset = self.before_filter_queryset(queryset, **kwargs)
        queryset = self._filter_queryset(queryset)

        # custom queryset handler
        queryset = self.handle_queryset(queryset, **kwargs)
        self.total_length = len(queryset)

        # pagination
        page_size = self.get_page_size()
        if page_size and not self.get_show_all():
            try:
                paginator, page, self.object_list, has_another_page = self.paginate_queryset(
                    queryset, page_size)
            except Http404:
                # this is for frontend pagination
                return list()
            self.paginator = paginator
            self.page = page
        else:
            self.object_list = queryset
        if self.paginator_class is MongoPaginator:
            # make collection result to list
            self.object_list = list(self.object_list)
        return self.object_list

    def handle_queryset(self, queryset, **kwargs) -> typing.Union[QuerySet, list]:
        """
        Write your logic here, e.g. process queryset again.

        The returned value must be an iterable object such as a queryset or list,
        as same as the argument queryset

        注意，如果要查询关联表信息（设置了related_sets和many_to_many_fields属性），
        需要返回queryset或包含了instance的列表，否则将不会查询关联表信息。你可以自己序列化成最终结果并返回。
        """
        return queryset

    def before_filter_queryset(self, queryset, **kwargs) -> typing.Union[QuerySet, list]:
        """
        Write your logic here, before filter queryset
        """
        return queryset

    def get_queryset(self):
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, models.QuerySet):
                # if self.related_sets:
                #     queryset = queryset.select_related(self.related_sets)
                # if self.many_to_many_fields:
                #     queryset = queryset.prefetch_related(self.many_to_many_fields)
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model._default_manager.all()
        elif self.paginator_class is MongoPaginator:
            if hasattr(self, 'collection'):
                assert (isinstance(self.collection, tuple) and
                        len(self.collection) == 2)
                db, col = self.collection
                queryset = MongoDB().col(db, col)
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a Mongo collection. "
                    "Define %(cls)s.collection." % {
                        'cls': self.__class__.__name__
                    }
                )
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )

        return queryset

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        return self.request.GET.get('orderBy') or self.ordering

    def get_page_size(self):
        return str2int(self.request.GET.get('pageSize'), default=10)

    def get_show_all(self):
        self.show_all = str2bool(self.request.GET.get('all', False))
        return self.show_all

    @staticmethod
    def _clean_query_value(value, field=None, refer_value=None,
                           iterable=False):
        """
        value_type is used for MongoDB data
        """
        if value == 'null':
            return None
        if iterable:
            # 转为可迭代对象
            value = str2iter(value)
        try:
            if isinstance(field, models.DateTimeField) or isinstance(refer_value, datetime.datetime):
                value = list(map(lambda x: to_aware_datetime(x), value)) if iterable else to_aware_datetime(value)
            elif isinstance(field, models.BooleanField) or isinstance(refer_value, bool):
                if iterable:
                    # bool filed not support iterable value
                    raise InvalidParameter(value)
                value = str2bool(value)
            elif isinstance(field, models.IntegerField) or isinstance(refer_value, int):
                value = list(map(lambda x: int(x), value)) if iterable else str2int(value)
            elif isinstance(field, models.FloatField) or isinstance(refer_value, float):
                value = list(map(lambda x: float(x), value)) if iterable else str2float(value)
            else:
                # str, bson ...
                pass
        except Exception:
            raise InvalidParameter(value)

        return value

    class FilterFormat(object):

        exc = 'exclude__'

        def __init__(self, name):
            self.isin = name + '__in'
            self.range = name + '__range'

            self.exact = name + '__exact'
            self.iexact = name + '__iexact'
            self.isnull = name + '__isnull'
            self.contains = name + '__contains'
            self.icontains = name + '__icontains'
            self.gt = name + '__gt'
            self.gte = name + '__gte'
            self.lt = name + '__lt'
            self.lte = name + '__lte'

        def exclude(self, cond):
            return self.exc + cond

    def _filter_queryset(self, queryset):
        """
        Filter queryset by layer, then by filter parameters and
        order queryset if necessary
        """

        # filtering except in case of passing parameter all=true
        query_data = self.request.GET
        if queryset.exists():
            ordering = self.get_ordering()
            if self.paginator_class is Paginator:
                meta = queryset[0]._meta
                fields = chain(meta.concrete_fields, meta.many_to_many)
                # try to get filters
                conditions = dict()
                exclude_cond = dict()
                for i, f in enumerate(fields):
                    name = f.attname
                    ff = self.FilterFormat(name)
                    if query_data.get(ff.isin):
                        conditions[ff.isin] = self._clean_query_value(
                            query_data.get(ff.isin), f, iterable=True)
                    if query_data.get(ff.range):
                        value = self._clean_query_value(
                            query_data.get(ff.range), f, iterable=True)
                        if isinstance(value, str) or len(value) != 2:
                            raise InvalidParameter(
                                _('Range must be a list with two elements.'))
                        conditions[ff.range] = value

                    if query_data.get(ff.isnull):
                        try:
                            cleaned_value = str2bool(query_data.get(ff.isnull))
                        except (TypeError, ValueError):
                            raise InvalidParameter(
                                _('isnull accepts only bool type'))
                        conditions[ff.isnull] = cleaned_value

                    common_cond = (
                        ff.exact, ff.iexact, ff.contains, ff.icontains,
                        ff.gt, ff.gte, ff.lt, ff.lte)
                    for item in common_cond:
                        if query_data.get(item):
                            conditions[item] = self._clean_query_value(
                                query_data.get(item), f)
                        elif query_data.get(ff.exclude(item)):
                            exclude_cond[item] = self._clean_query_value(
                                query_data.get(ff.exclude(item)), f)
                queryset = queryset.exclude(**exclude_cond).filter(**conditions)

                if ordering:
                    if isinstance(ordering, str):
                        ordering = (ordering,)
                    queryset = queryset.order_by(*ordering)

                self.total_length = queryset.count()

            elif self.paginator_class is MongoPaginator:
                conditions = dict()
                # col = getattr(self, 'collection')
                first_item = queryset.find_one()
                if first_item:
                    for name, v in first_item.items():
                        ff = self.FilterFormat(name)
                        if query_data.get(ff.isin):
                            value = self._clean_query_value(
                                query_data.get(ff.isin), refer_value=v,
                                iterable=True)
                            conditions[name] = {'$in': value}
                        elif query_data.get(ff.range):
                            value = self._clean_query_value(
                                query_data.get(ff.range), refer_value=v,
                                iterable=True)
                            if isinstance(value, str) or len(value) != 2:
                                raise InvalidParameter(
                                    _('Range must be a list with two elements.'))
                            _cond = {'$gte': value[0], '$lte': value[1]}
                            conditions.update({name: _cond})
                        elif query_data.get(ff.isnull):
                            value = str2bool(query_data.get(ff.isnull))
                            conditions.update({name: value})
                        for item in (ff.exact, ff.gt, ff.gte, ff.lt, ff.lte, ff.contains):
                            if query_data.get(item):
                                value = self._clean_query_value(
                                    query_data.get(item), refer_value=v)
                                if item == ff.exact:
                                    conditions.update({name: value})
                                else:
                                    _cond = dict()
                                    if item == ff.gt:
                                        _cond.update({'$gt': value})
                                    elif item == ff.gte:
                                        _cond.update({'$gte': value})
                                    elif item == ff.lt:
                                        _cond.update({'$lt': value})
                                    elif item == ff.lte:
                                        _cond.update({'$lte': value})
                                    elif item == ff.contains:
                                        _cond.update({'$regex': value})
                                    conditions.update({name: _cond})
                            if item in (ff.icontains, ff.iexact):
                                if query_data.get(item):
                                    raise InvalidParameter(_(''))
                    # conditions.update({'object_name': {'$ne': ''}})
                    queryset = queryset.find(conditions)
                    if queryset:
                        if ordering:
                            if ordering.startswith('-'):
                                queryset = queryset.sort(ordering[1:], -1)
                            else:
                                queryset = queryset.sort(ordering)
        return queryset


class DetailView(ResponseMixin, BaseViewMixin, _DetailView):
    http_method_names = ['get']
    related_sets: tuple = None
    many_to_many_fields = tuple = None
    disable_object_permission = False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_json_response(data=self.object)


class CreateView(ResponseMixin, BaseViewMixin, FormValidationMixin,
                 _CreateView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # request._opt_data and request._opt_save are used to write operation log when came into exceptions
        # We don't know the object name until saved it, use verbose_name instead of it
        self.object = None

        form = self.get_form()
        if form.is_valid():
            response = self.form_valid(form)
            return response
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # mainly used for post_save signal
        form.instance.request_user = self.request.user
        return super().form_valid(form)


class UpdateView(ResponseMixin, BaseViewMixin, FormValidationMixin,
                 _UpdateView):
    http_method_names = ['put', 'post']

    def put(self, *args, **kwargs):
        self.request.POST = QueryDict(self.request.body)
        return super().put(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class DeleteView(ResponseMixin, BaseViewMixin, _DeleteView):
    http_method_names = ['delete']

    def before_delete(self, *args, **kwargs) -> None:
        """
        Extra validation method or do something (handle queryset) before deleting.
        Write your logic here, before deleting objects.
        """
        pass

    def after_delete(self, *args, **kwargs) -> None:
        """Do something after deleting"""
        pass

    def _delete(self):
        self.object.delete()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # prepare for operation log

        self.object.request_user = self.request.user

        self.before_delete(*args, **kwargs)
        self._delete()
        self.after_delete(*args, **kwargs)
        return self.render_to_json_response(data=self.object)


class BulkDeleteView(DeleteView):
    def get_queryset(self):
        if self.queryset is None:
            if hasattr(self, 'model') and self.model:
                if not hasattr(self, 'pks'):
                    raise ImproperlyConfigured(
                        'pks must be defined before getting queryset')
                if hasattr(self, 'primary_key'):
                    kwargs = {self.primary_key + '__in': self.pks}
                elif self.slug_url_kwarg and self.slug_url_kwarg != 'slug':
                    kwargs = {self.slug_field: self.slug_url_value}
                else:
                    kwargs = {'pk__in': self.pks}

                # set layer type and id, used to deal with LayerResource
                # self.model.layer_type = self.request.layer.type
                # self.model.layer_id = self.request.layer.id

                return self.model._default_manager.filter(**kwargs)
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.queryset

    def get_validated_queryset(self, **kwargs):
        pks = kwargs.get(self.pk_url_kwarg)
        if not isinstance(pks, list):
            if not (hasattr(self, 'slug_url_kwarg') and self.slug_url_kwarg != 'slug'):
                raise ImproperlyConfigured(
                    _('%(pk_url_kwarg)s is not a proper pk_url_kwarg.') %
                    {'pk_url_kwarg': self.pk_url_kwarg})
            self.slug_url_value = kwargs.get(self.slug_url_kwarg)
        self.pks = pks
        self.queryset = self.get_queryset()

        if not hasattr(self, 'slug_url_value') and self.queryset.count() < len(pks):
            pk = getattr(self, 'primary_key') if hasattr(self, 'primary_key') else 'pk'
            item_pks = [getattr(item, pk) for item in self.queryset]
            not_exist = map(lambda x: str(x), filter(lambda x: x not in item_pks, pks))
            raise self.model.DoesNotExist(','.join(not_exist))
        return self.queryset

    def _delete(self):
        """
        Rewrite this method if you dot NOT want to delete queryset
        """
        self.queryset.delete()

    def delete(self, request, *args, **kwargs):
        """
        Multiple OpenStack objects deleting example:

        self.get_validated_queryset(**kwargs)
        for item in self.queryset:
            driver.delete()
            item.delete()
        return self.render_to_json_response()
        """
        self.get_validated_queryset(**kwargs)
        self.before_delete(*args, **kwargs)

        # prepare operation log
        # objs_str = ', '.join([obj.__str__() for obj in self.queryset]).rstrip()
        # custom log

        # reserve a list of queryset which can be used in next steps
        self.queryset_list = queryset_to_list(self.queryset)
        if not hasattr(self, 'pks') or not self.pks:
            self.pks = list(self.queryset.values_list('pk', flat=True))

        for obj in self.queryset:
            obj.request_user = self.request.user
        # queryset delete
        self._delete()

        self.after_delete(*args, **kwargs)

        return self.render_to_json_response(data=self.queryset_list)
