

def get_absolute_url(request, url):
    protocol = 'https' if request.is_secure() else 'http'
    return '%s://%s%s' % (protocol, request.META['HTTP_HOST'], url)
