"""
Create middleware here, don't forget to add it to the MIDDLEWARE list
in your Django settings.

Reference:
https://docs.djangoproject.com/en/2.0/topics/http/middleware/

"""

import traceback

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError, PermissionDenied
from django.http.response import JsonResponse, Http404
from django.middleware.csrf import CsrfViewMiddleware as _CsrfViewMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.utils.log import log_response
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from common.core.exceptions import SException
from common.log import default_logger as logger
from common.mixin.json import ret_format, exception_to_response


class ExceptionProcessingMiddleware(MiddlewareMixin):

    # def __init__(self, get_response):
    #     # self.get_response = get_response
    #     self.mongo_log_db = MongoDB().col_opt_log()
    #     super().__init__(get_response)
    #     # One-time configuration and initialization.
    #     # Initialize first starting of the system

    # def __call__(self, request):
    #     # Code to be executed for each request before
    #     # the view (and later middleware) are called.
    #     super().__call__(request)
    #     response = self.get_response(request)
    #
    #     # Code to be executed for each request/response after
    #     # the view is called.
    #
    #     return response

    # def process_view(self, request, view_func, *view_args, **view_kwargs):
    #     """
    #     call before view executing
    #     """
    #     pass

    def process_exception(self, request, exception):
        """
        Call when raise an exception
        """
        if isinstance(exception, SException):
            # log by level
            if exception.level == 'error':
                logger.error(request)
                logger.error(str(traceback.format_exc()))
            elif exception.level == 'warning':
                logger.warn(str(exception))
            elif exception.level == 'info':
                logger.info(str(exception))

            # response distinctively
            return exception_to_response(exception)
        else:
            # django/others exceptions
            code = 500
            level = 'error'
            data = None
            if isinstance(exception, PermissionDenied):
                messages = _('Permission denied')
                level = 'warning'
                code = 403
            elif isinstance(exception, (ObjectDoesNotExist, Http404)):
                messages = list()
                for item in exception.args:
                    p = ' matching query does not exist.'
                    msg = _('%(item)s' + p) % {'item': _(item.replace(p, '').strip().lower())}
                    messages.append(format_lazy('{}: {}', _('No such object'), msg))
                    logger.error(traceback.format_exc())
                level = 'error'
                code = 404
            elif isinstance(exception, KeyError):
                messages = list()
                for item in exception.args:
                    messages.append(_('Key error: %(item)s does not exist.') % {'item': item})
                logger.error(traceback.format_exc())
                code = 400
            elif isinstance(exception, ValidationError):
                code = 402
                messages = exception.message
            else:
                messages = str(exception)
                logger.error(messages)
                logger.error(traceback.format_exc())
            return JsonResponse(
                ret_format(result=False, messages=messages,
                           code=code, level=level, data=data)
            )

    # def process_request(self, request):
    #     """
    #     Call before processing view
    #     Can modify request
    #     """
    #     pass

    # def process_response(self, request, response):
    #     """
    #     Call after view finished
    #     """
    #     return response

    # def process_template_response(self, request, response):
    #     """
    #     call after view finished
    #     objects returned by view must contain render method, such as
    #     django.template.response.TemplateResponse
    #     """
    #
    #     return response


class LoggingMiddleware(MiddlewareMixin):

    @staticmethod
    def wrap_streaming_content(content):
        for chunk in content:
            yield chunk

    def _log_request_and_response(self, request, response):
        # log every request & response
        if isinstance(response, JsonResponse):
            log_req = '%(scheme)s %(method)s %(status_code)d %(path)s [%(remote_host)s:%(remote_port)s]' % (
                {'scheme': request.scheme.upper(), 'method': request.method, 'status_code': response.status_code,
                 'path': request.path,
                 'remote_host': request.META.get('REMOTE_HOST') or request.META.get('REMOTE_ADDR'),
                 'remote_port': request.META.get('REMOTE_PORT') or request.META.get('SERVER_PORT')})
            if request.method == 'POST' and settings.DEBUG:
                log_req += ' '
                log_req += str(request.POST.dict())
            logger.debug(log_req)
            if response.streaming:
                # fixme: log streaming response
                # log_res = self.wrap_streaming_content(response.streaming_content)
                pass
            elif settings.DEBUG:
                log_res = str(response.content.decode('utf-8'))
                log_res = ('%s ... (%d omitted)' % (log_res[:1000], len(log_res) - 1000)
                           if len(log_res) > 1000 else log_res)
                logger.debug(log_res)

    # def process_request(self, request):
    #     if request.META['PATH_INFO'] in self.ignore_paths:
    #         return HttpResponse()

    def process_response(self, request, response):
        # if settings.DEBUG is True:
        self._log_request_and_response(request, response)
        return response


class CsrfViewMiddleware(_CsrfViewMiddleware):

    def _reject(self, request, reason):
        # response = _get_failure_view()(request, reason=reason)
        response = JsonResponse(
            ret_format(
                result=False,
                messages='CSRF validation error',
                level='error', code=420
            )
        )
        log_response(
            'Forbidden (%s): %s', reason, request.path,
            response=response,
            request=request,
            logger=logger,
        )
        return response
