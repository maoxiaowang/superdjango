from django.http.response import (
    HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest
)
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import (
    page_not_found as _page_not_found)
from django.core.cache import cache

from common.mixin import ResponseMixin
from common.views.general import *

__all__ = [
    'page_not_found', 'bad_request', 'permission_denied', 'server_error',
    'View', 'FormView', 'TemplateView',
    'AdvancedListView', 'BulkDeleteView',
    'ListView', 'CreateView', 'DetailView', 'UpdateView', 'DeleteView',
]

JRM = ResponseMixin()


@requires_csrf_token
def page_not_found(request, exception, template_name='404.html'):
    if request.is_ajax():
        return JRM.render_to_json_response(code=404, messages=_('Page not found'))
    else:
        return _page_not_found(request, exception, template_name=template_name)


@requires_csrf_token
def bad_request(request, exception, template_name='400.html'):
    if request.is_ajax():
        return JRM.render_to_json_response(code=400, messages=_('Bad request'))
    else:
        template = loader.get_template(template_name)
        return HttpResponseBadRequest(template.render({'site': cache.get('site')}))


@requires_csrf_token
def permission_denied(request, exception, template_name='403.html'):
    if request.is_ajax():
        return JRM.render_to_json_response(code=403, messages=_('权限不足'))
    else:
        template = loader.get_template(template_name)
        return HttpResponseForbidden(
            template.render(
                request=request,
                context={
                    'exception': str(exception),
                    'site': cache.get('site')
                }
            )
        )


@requires_csrf_token
def server_error(request, template_name='500.html'):
    if request.is_ajax():
        return JRM.render_to_json_response(code=500, messages=_('Server error'))
    else:
        template = loader.get_template(template_name)
        return HttpResponseServerError(template.render({'site': cache.get('site')}))


def csrf_failure(request, reason=None):
    template = loader.get_template('403_csrf.html')
    return HttpResponseForbidden(
        template.render(
            request=request,
            context={
                # 'site': cache.get('site')
                'reason': reason
            }
        )
    )
