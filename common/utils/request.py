import uuid
from django.contrib.auth.models import AnonymousUser


def get_remote_ip_address(request):
    return (
        request.META.get('HTTP_X_FORWARDED_FOR').split(',')[0]
        if request.META.get('HTTP_X_FORWARDED_FOR') else request.META.get('REMOTE_ADDR')
    ) if hasattr(request, 'META') else None


def get_remote_mac_address(request):
    """
    Fixme: get from headers
    """
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    return "-".join([mac[e:e + 2] for e in range(0, 11, 2)])


def request_factory(method, user=None):
    """
    构造简单的request，用于操作日志
    """
    method = method.upper()
    assert method in ['GET', 'POST', 'PUT', 'DELETE']
    if user is None:
        user = AnonymousUser()
        user.username = 'ECloud'
        user.role_name = '平台'

    class Meta:
        REMOTE_ADDR = '127.0.0.1'

    return type('Request', (object,), {'method': method, 'user': user, 'Meta': Meta})()
