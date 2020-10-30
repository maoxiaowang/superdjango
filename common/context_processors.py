"""
https://docs.djangoproject.com/en/2.0/ref/templates/api/#using-requestcontext

Do not forget to set in settings.py
"""
import time


def default(request):
    """
    :param request:
    :return: a dict
    """
    # template styles according to user's settings
    result = dict(user_settings={})

    result['timestamp'] = int(time.time())
    return result
