from django.middleware.csrf import get_token
from django.views.generic.base import View as _View

from base.forms import *
from base.models import SystemSettings
from common.core.cache import queryset_cache
from common.mixin import ResponseMixin, LoginRequiredMixin, PermissionRequiredMixin
from common.views import UpdateView, AdvancedListView, View


class GetCSRFToken(ResponseMixin, _View):
    """
    获取新的CSRF Token
    """
    http_method_names = ['get']

    def get(self, request):
        token = get_token(request)
        response = self.render_to_json_response()
        response.set_cookie('csrftoken', token)
        return response


class SystemSettingsList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    系统设置列表
    """
    author = 'Oliver'
    updated_at = '2020.02.23'
    model = SystemSettings
    permission_required = 'base.view_system_settings'


class SystemSettingsUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    更改系统设置
    """
    model = SystemSettings
    form_class = SystemSettingsUpdateForm
    slug_field = 'key'
    slug_url_kwarg = 'key'
    permission_required = 'base.change_system_settings'

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.object = self.object
        return form


class DatabaseCacheKeys(LoginRequiredMixin, View):
    """
    数据库缓存所有的键
    """

    def get(self, request, *args, **kwargs):
        return self.render_to_json_response(
            data=list(queryset_cache.__dir__())
        )


class DatabaseCache(LoginRequiredMixin, View):
    """
    查询数据库缓存
    """

    def get(self, request, *args, **kwargs):
        app_model = kwargs.get('app_model')
        queryset = getattr(queryset_cache, app_model, None)
        if queryset is None:
            return self.render_to_json_response(
                result=False, messages="No such app-model '%s'." % app_model
            )
        return self.render_to_json_response(data=queryset)
