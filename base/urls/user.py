from django.urls import path
from base.views import user

urlpatterns = [
    # base
    path('user/list/', user.UserList.as_view(), name='user_list'),
    path('user/<int:user_id>/detail/', user.UserDetail.as_view(), name='user_detail'),
    path('user/who-am-i/', user.WhoAmI.as_view()),
    path('user/create/', user.UserCreate.as_view(), name='user_create'),
    path('user/<int:user_id>/update/', user.UserUpdate.as_view(), name='user_update'),
    path('user/<int:user_id>/delete/', user.UserDelete.as_view(), name='user_delete'),
    path('user/<int:user_id>/roles/update/', user.UserRoleUpdate.as_view(), name='user_roles_update'),
    path('user/<int:user_id>/lock/', user.Lock.as_view(), name='lock_user'),
    path('user/<int:user_id>/active/', user.Active.as_view(), name='active_user'),

    # identity
    path('user/login/', user.Login.as_view(), name='user_login'),
    path('user/logout/', user.Logout.as_view(), name='user_logout'),
    path('user/change-password/', user.ChangePassword.as_view(), name='user_change_password'),
    path('user/set-password/', user.SetPassword.as_view(), name='user_set_password'),

    # security
    # path('user/address-control/list/', user.AddressControlList.as_view()),
    # path('user/address-control/create/', user.AddressControlCreate.as_view()),
    # path('user/<int:user_id>/login-period/detail/', user.LoginPeriodDetail.as_view()),
    # path('user/login-period/<int:pk>/update/', user.LoginPeriodUpdate.as_view()),
    path('user/address-control/<int:pk>/delete/', user.AddressControlDelete.as_view()),

    # login-limit
    path('user/<int:user_id>/login-limit/detail/', user.LoginLimitDetail.as_view(), name='login_limit_detail'),
    path('user/login-limit/edit/', user.LoginLimitEdit.as_view(), name='login_limit_edit')

]
