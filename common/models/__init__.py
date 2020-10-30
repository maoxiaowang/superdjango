from importlib import import_module

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

__all__ = [
    'models',
    'ct'
]


class Models(object):
    """
    Dynamically load a model or its content type.

    - Usage:
    from common.models import models
    model_cls = models.APP_NAME.MODEL_NAME
    model_ct_cls = model_cls._ct
    """

    class Model(object):
        app_name = None

        def __getattr__(self, name):
            """
            Get model of an app
            """
            if name == '_set_content_type':
                return object.__getattribute__(self, name)
            model_module = import_module('{0}.models'.format(self.app_name))
            try:
                model_cls = getattr(model_module, name)
            except AttributeError:
                raise ImportError(
                    "can not import model named '{0}' from '{1}'".format(
                        name, model_module.__name__
                    )
                )
            model_cls = self._set_content_type(model_cls)
            return model_cls

        @staticmethod
        def _set_content_type(model_cls):
            _ct = ContentType.objects.get_for_model(model_cls)
            setattr(model_cls, '_ct', _ct)
            return model_cls

    def __init__(self):
        self.ct_model = ContentType
        self.models = None

    def __dir__(self):
        mappings = dict()
        if self.models is None:
            self.models = apps.get_models()
        for model in self.models:
            app = model._meta.app_config
            mappings.update({app.name: getattr(self, app.name)})
        return self.mappings.keys()

    def __getattr__(self, app_name):
        """
        Get app object
        """
        app = type(app_name, (self.Model,), dict(app_name=app_name))()
        return app


models = Models()


class CType(object):
    """
    Dynamically get content type of a model.

    - Usage:
    from common.helpers.content_type import CT
    CT.compute.Instance => <ContentType: instance>
    CT.network.Subnet => <ContentType: subnet>
    ...

    from compute.models import Instance
    CT.get(Instance) => <ContentType: instance>
    ...

    ** NOTICE **
    Do Not forget to import your model class to __init__.py if the models
    is created as a package.
    """
    models = None
    ct_model = ContentType

    class Model(object):
        app_name = None

        def __getattr__(self, model_name):
            """
            Get model content type of an app
            """
            model_module = import_module('{0}.models'.format(self.app_name))
            # You can use lower case model class name
            try:
                model_cls = getattr(model_module, model_name)
            except AttributeError:
                raise ImportError(
                    "can not import model named '{0}' from '{1}'".format(
                        model_name, model_module.__name__
                    )
                )
            return ContentType.objects.get_for_model(model_cls)

    def __dir__(self):
        mappings = dict()
        if self.models is None:
            self.models = apps.get_models()
        for model in self.models:
            app = model._meta.app_config
            mappings.update({app.name: getattr(self, app.name)})
        return self.mappings.keys()

    def __getattr__(self, app_name):
        """
        Get app object
        """
        app = type(app_name, (self.Model,), dict(app_name=app_name))()
        return app


ct = CType()
