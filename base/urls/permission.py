from django.urls import path

from base.views import permission

urlpatterns = [
    path('permission/list/', permission.PermissionsList.as_view(), name='permission_list'),


]
