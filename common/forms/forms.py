import functools

__all__ = [
    'FormMixin',
]

from django.utils.decorators import method_decorator


def change_auto_id(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        res.auto_id = self.__class__.__name__.lower() + '_%s'
        return res

    return inner


@method_decorator(change_auto_id, name='__init__')
class FormMixin:
    """
    用于
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_id = self.__class__.__name__.lower() + '_%s'
