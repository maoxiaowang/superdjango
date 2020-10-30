import os

from django.apps import AppConfig

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class BaseConfig(AppConfig):
    name = 'base'

    def ready(self):
        # create media directory if it is necessary
        # media_path = os.path.join(BASE_DIR, 'media')
        # if not os.path.exists(media_path):
        #     os.makedirs(media_path)

        # don't move
        import base.signals.handlers
        base.signals.handlers.foo()
