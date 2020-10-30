from django.urls import path

from base.views import role

urlpatterns = [
    path('role/list/', role.RoleList.as_view(), name='role_list'),
    path('role/create/', role.RoleCreate.as_view(), name='role_create'),
    path('role/<int:role_id>/update/', role.RoleUpdate.as_view(), name='role_update'),
    path('role/<int:role_id>/delete/', role.RoleDelete.as_view(), name='role_delete'),
    path('role/<int:role_id>/users/add/', role.RoleUsersAdd.as_view(), name='role_users_add'),
    path('role/<int:role_id>/users/remove/', role.RoleUsersRemove.as_view(), name='role_users_remove'),
    path('role/<int:role_id>/users/list/', role.RoleUsersList.as_view(), name='role_users_list'),
    # path('role/<int:role_id>/perms/add/', role.RolePermsAdd.as_view(), name='role_perms_add'),
    # path('role/<int:role_id>/perms/remove/', role.RolePermsRemove.as_view(), name='role_perms_remove'),
    path('role/<int:role_id>/perms/list/', role.RolePermsList.as_view(), name='role_perm_list'),
]
