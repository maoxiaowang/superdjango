import typing
import warnings

from django.apps import apps
from django.conf import settings
from django.core.cache import cache, caches
from django.db.models.base import ModelBase

from common.utils.general import ClsHelper

__all__ = [
    'GenericBasedCache',
    'ModelBasedCache',
    'queryset_cache'  # a shortcut
]


if not settings.configured:
    settings.configure()


class GenericBasedCache(object):

    def __init__(self, name: str, driver='default'):
        assert driver in ('default', 'redis')
        self.cache = caches[driver]
        self.name = name

    def get(self, default=None, **kwargs):
        value = self.cache.get(self.name)
        if value is None and default:
            # cache not exists
            if callable(default):
                value = default(**kwargs)
                self.set(value)
                return default(**kwargs)
            self.set(default)
            return default
        return value

    def set(self, value: str, timeout: int = None):
        """
        Caution: if you set timeout to an integer,
        you should not forget to update your cache manually,
        or the cache will expire after given time.
        """
        self.cache.set(self.name, value, timeout)


class ModelBasedCache(object):
    """
    用于缓存一个queryset数据，func函数默认None时返回queryset.all()
    """

    def __init__(self, model_cls: typing.Union[ModelBase, str],
                 timeout: typing.Union[None, int] = 30,
                 func=None, **kwargs):
        """
        models_cls: APP_NAME.MODEL_NAME 或 Model类
        timeout: 缓存超时时间
        ---
        The default timeout, in seconds, to use for the cache.
        This argument defaults to 300 seconds (5 minutes).
        You can set TIMEOUT to None so that, by default, cache keys never expire.
        A value of 0 causes keys to immediately expire (effectively “don’t cache”).
        ---

        func默认是不带参数的函数，如果需要自定义参数，配合args和kwargs参数使用
        args: func的位置参数
        kwargs: func的关键字参数
        """
        self.model_cls = apps.get_model(model_cls) if isinstance(model_cls, str) else model_cls
        self.name = '%s_%s' % (self.model_cls._meta.app_label, self.model_cls.__class__.__name__)
        self.timeout = timeout
        # self.host = default_settings['host']  # multiple developments
        self.func = func
        self.disable_warnings = kwargs.get('disable_warnings', False)

    def _get_from_db(self, func, *args, **kwargs):
        if func:
            if callable(func):
                return func(*args, **kwargs)
            return func
        return self.model_cls._meta.default_manager.all()

    def _get_key(self, identifiers):
        conn = '_'
        # name = self.host + conn + self.name
        name = self.name
        if not identifiers:
            return name
        try:
            return name + conn + identifiers
        except TypeError:
            assert isinstance(identifiers, typing.Iterable), (
                    'The value of identifiers must be iterable, not type of %s.'
                    % type(identifiers).__name__
            )
            key = name + conn
            key += conn.join(identifiers)
            return key

    def get(self, identifiers: typing.Union[str, typing.Iterable] = None, func=None,
            *args, **kwargs):
        """
        获取缓存的数据，当没有缓存数据时，从数据库查询，当存在func时通过其查询结果

        identifier是一个或多个动态的字符串用于细分每个缓存（比如可以是不同用户的名字），强烈建议，否则可能导致数据错误
        其他参数同构造器
        """
        data = cache.get(self._get_key(identifiers))
        func = func or self.func
        if data is None:
            data = self._get_from_db(func, *args, **kwargs)
            self.set(identifiers=identifiers, func=func, *args, **kwargs)
        return data

    def set(self, identifiers: typing.Union[str, typing.Iterable] = None, func=None,
            *args, **kwargs):
        """
        手动更新缓存数据

        参数同get
        """
        if not identifiers and not self.disable_warnings:
            warnings.warn('An unique identifier is strongly recommended.', UserWarning)
        func = func or self.func
        # 0 means cache without timeout
        cache.set(self._get_key(identifiers), self._get_from_db(func, *args, **kwargs), self.timeout)


class QuerySetCache(ClsHelper):
    """
    This Class used to cache queryset of model.

    Usage:

    1. Define an attribute (form like app_label.model_name) of the class
    and add string of it in cached_models (value is seconds of timeout).

    class QuerySetCache(object):
        _cached_models = {
            # Define cache models here, {APP_NAME.MODEL_NAME, TIMEOUT)
            'base.Group': 30,
            'base.User': 10,
            'base.OperationLogEntry': 5,
        }

    If _cached_models is defined, attributes will be restrict by it.
    On contrary, if it is not defined, all app model attributes is available.

    2. Import queryset_cache to your file and use it.

    from common.core.cache import queryset_cache

    users_logged_in_this_year = queryset_cache.base_User.filter(
        last_login__year=timezone.now().year
    )

    Alternatively you can define a new class inherits from QuerySetCache and use it.

    [NOTICE]
    To make this class effective, please make sure all apps and models you use here
    not contains underline.
    """
    _default_timeout: int = 10

    # fixme: add more -> APP_NAME_MODEL_NAME = TIMEOUT
    base_Group: int = 30
    base_User = 10
    base_Permission = None  # None means will not timeout
    # If you define an attribute to use a model cache and set it to None, please update
    # cache in signals respectively. If it was set to 0, that model will never be cached.

    # Optional restriction attributes
    # _cached_models = {
    #     # Define available models here, {APP_NAME.MODEL_NAME, TIMEOUT)
    #     'base.Group': 30,
    #     'base.User': 10,
    # }

    def __init__(self):
        super().__init__()
        named_mappings = dict()
        if self._cached_models:
            # some restriction
            for app_model, timeout in self._cached_models.items():
                app_name, model_name = app_model.split('.')
                app_models = apps.all_models.get(app_name)
                if not app_models.get(model_name.lower()):
                    raise LookupError('Model %s.%s does not exist.' % (app_name, model_name))
                named_mappings['{0}_{1}'.format(app_name, model_name)] = timeout
        else:
            for app_name, models in apps.all_models.items():
                for _, model_cls in models.items():
                    app_model = '{0}_{1}'.format(app_name, model_cls.__name__)
                    named_mappings[app_model] = self._get_timeout(app_model)
        object.__setattr__(self, '_named_mappings', named_mappings)
        for key in self.all_keys():
            if key not in named_mappings:
                warnings.warn('%s is not a valid attribute.' % key, UserWarning)

    def __new__(cls, *args, **kwargs):
        cached_models = cls._cached_models if hasattr(cls, '_cached_models') and cls._cached_models else dict()
        setattr(cls, '_cached_models', cached_models)
        # check cached models
        for app_model in cls._cached_models.keys():
            try:
                _a, _m = app_model.split('.')
            except ValueError:
                raise ValueError("'%s' is not of the form 'app_label.model_name'." % app_model)
        return super().__new__(cls)

    def __getattribute__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._named_mappings.keys():
            model_cls = self._get_model_cls(name)
            try:
                timeout = object.__getattribute__(self, name)
            except AttributeError:
                timeout = self._default_timeout
            return ModelBasedCache(model_cls, timeout=timeout).get(name)
        return object.__getattribute__(self, name)

    def __dir__(self):
        return self._named_mappings.keys()

    def _get_timeout(self, app_model):
        try:
            return getattr(self, app_model)
        except AttributeError:
            return self._default_timeout

    @staticmethod
    def _get_model_cls(attr):
        for app_name, models in apps.all_models.items():
            for _, model_cls in models.items():
                app_model = '{0}.{1}'.format(app_name, model_cls.__name__)
                if app_model.replace('.', '_') == attr:
                    return apps.get_model(app_model)
        raise AttributeError


queryset_cache = QuerySetCache()
