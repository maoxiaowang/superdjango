from django.urls import path

from base.urls.opt_log import urlpatterns as opt_log_patterns
from base.urls.permission import urlpatterns as permission_patterns
from base.urls.role import urlpatterns as role_patterns
from base.urls.user import urlpatterns as user_patterns
from base.urls.resource import urlpatterns as resource_patterns
from base.views import (
    GetCSRFToken, SystemSettingsUpdate, SystemSettingsList, DatabaseCache, DatabaseCacheKeys
)

app_name = 'base'

urlpatterns = [
    path('get_token/', GetCSRFToken.as_view(), name='get_csrf_token'),
    path('settings/list/', SystemSettingsList.as_view(), name='system_settings_list'),
    path('settings/<slug:key>/update/', SystemSettingsUpdate.as_view(), name='system_settings_update'),
    # path('db-cache/<slug:app_model>/', DatabaseCache.as_view(), name='db_cache'),
    # path('db-cache-keys/', DatabaseCacheKeys.as_view(), name='db_cache_keys'),
]

urlpatterns += user_patterns
urlpatterns += opt_log_patterns
urlpatterns += permission_patterns
urlpatterns += role_patterns
urlpatterns += resource_patterns
