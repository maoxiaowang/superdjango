from django.db.models.signals import post_save
from django.dispatch import receiver

from base.models.user import User


def foo():
    pass


@receiver(post_save, sender=User)
def on_user_saved(sender, instance, **kwargs):
    if kwargs.get('created'):
        ...
