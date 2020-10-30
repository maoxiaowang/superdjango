from django.dispatch import Signal


password_update_end = Signal(providing_args=['user'])
