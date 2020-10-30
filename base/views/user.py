from django.contrib.auth import login, views as auth_views, update_session_auth_hash, logout
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.http import HttpResponseRedirect, QueryDict
from base.exceptions import NeedChangePassword
from base.forms.user import (
    UserLoginForm, UserCreatForm, UserUpdateForm, UserRoleUpdateForm, SetPasswordForm,
    ChangePasswordForm, AddressControlForm, LoginPeriodUpdateForm, LoginLimitEditForm)
from base.helpers.user import idle_time_is_out
from base.managers import OptLogManager
from base.models import User, AddressControl, LoginPeriod, Resource
from base.models.user import LoginTerminal
from base.signals import password_update_end
from base.constants import BUILT_IN_USER_NAMES
from common.core.exceptions import OperationNotAllowed
from common.forms import Serializer, model_to_dict, queryset_to_list
from common.mixin import ResponseMixin, FormValidationMixin, PermissionRequiredMixin, LoginRequiredMixin, BaseViewMixin
from common.views.general import (
    AdvancedListView, DeleteView, UpdateView, FormView, CreateView, DetailView, View)


class Login(BaseViewMixin, ResponseMixin, FormValidationMixin, auth_views.LoginView):
    """
    用户登录，保持会话时间和配置有关，默认为1天。
    若设置keep_login=true，则保持会话30天。
    """
    http_method_names = ['post']
    authentication_form = UserLoginForm
    redirect_authenticated_user = False

    # def post(self, request, *args, **kwargs):
    #     user = AnonymousUser()
    #     user.username = request.POST.get('username')
    #     self.opt_logger._request.user = user
    #     self.request.opt_obj = self.opt_logger.info(
    #         request.POST.get('username'), '用户登录', action='登录', model=User)
    #     return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        request_user = form.get_user()
        self.opt_logger._request.user = request_user
        # opt_log
        self.request.opt_obj = self.opt_logger.info(request_user, '用户登录', action='登录')
        # 首次登录需修改密码
        if request_user.password_updated_at is None:
            return self.render_to_json_response(
                result=False,
                code=NeedChangePassword.code,
                messages=NeedChangePassword.desc,
                data=request_user
            )

        login(self.request, request_user)

        # keep login
        if form.cleaned_data.get('keep_login'):
            # session will expire on closing browser
            self.request.session.set_expiry(
                timezone.timedelta(days=30).total_seconds()
            )

        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, request_user)
        data = model_to_dict(request_user, related_sets=('groups',))
        return self.render_to_json_response(data=data)


class Logout(ResponseMixin, BaseViewMixin, auth_views.LogoutView):
    """
    用户登出
    """
    http_method_names = ['post']

    def dispatch(self, request, *args, **kwargs):
        # opt_log
        self.opt_logger = OptLogManager(request)
        if request.user.id is not None:
            self.request.opt_obj = self.opt_logger.info(request.user, '用户登出', action='登出', model=User)
        logout(request)
        next_page = self.get_next_page()
        if next_page:
            # 重定向
            return HttpResponseRedirect(next_page)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_json_response()


class Active(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    激活/禁用用户
    1：激活
    0：禁用
    """
    http_method_names = ['put']
    permission_required = 'base.active_user'
    model = User
    pk_url_kwarg = 'user_id'
    fields = ('is_active',)

    def post(self, request, *args, **kwargs):
        # opt_log
        user = User.objects.get(pk=kwargs.get('user_id'))
        if kwargs.get('is_active') == 1:
            content = '激活用户'
        else:
            content = '禁用用户'
        self.opt_logger.info(user, content=content, remarks='激活/禁用用户')
        return super().post(request, *args, **kwargs)


class Lock(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    锁定/解锁用户
    0：未锁定
    1：锁定
    """
    http_method_names = ['put']
    permission_required = 'base.lock_user'
    model = User
    pk_url_kwarg = 'user_id'
    fields = ('is_locked',)

    def post(self, request, *args, **kwargs):
        # opt_log
        user = User.objects.get(pk=kwargs.get('user_id'))
        if kwargs.get('is_active') == 0:
            content = '解锁用户'
        else:
            content = '锁定用户'
        self.opt_logger.info(user.username, content=content, remarks='激活/禁用用户', model=User)
        return super().post(request, *args, **kwargs)


class WhoAmI(View):

    def get(self, request):
        return self.render_to_json_response(data=self.request.user)


class UserList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    列出所有用户
    """
    model = User
    permission_required = 'base.list_user'
    ordering = ('-id',)
    related_sets = ('groups',)

    def get_queryset(self):
        return super().get_queryset().exclude(is_deleted=True)

    def handle_queryset(self, queryset, **kwargs):
        # superuser仅用于开发，对用户不可见
        users = Serializer(
            queryset, exclude='is_deleted',
            related_sets=self.related_sets,
        ).to_python()
        for user in users:
            is_online = not idle_time_is_out(user)
            user.update(is_online=is_online)
            # 目前只能有一个角色
            user['groups'] = user['groups'][0] if user['groups'] else None
        return users


class UserDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    用户详情
    """
    model = User
    permission_required = 'base.detail_user'
    pk_url_kwarg = 'user_id'
    related_sets = ('groups',)


class UserCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    创建用户
    """
    http_method_names = ['post']
    model = User
    form_class = UserCreatForm
    permission_required = 'base.create_user'

    def form_valid(self, form):
        # opt_log
        self.request.opt_obj = self.opt_logger.info(form.cleaned_data['username'], content='创建用户', action='创建用户',
                                                    model=User)
        form.instance.email = form.cleaned_data['username'] + '@example.com'
        return super().form_valid(form)


class UserDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    删除用户
    """
    model = User
    pk_url_kwarg = 'user_id'
    permission_required = 'base.delete_user'

    def get_queryset(self):
        # opt_log
        self.request.opt_obj = self.opt_logger.info(User.objects.get(pk=self.kwargs.get('user_id')), content='删除用户',
                                                    action='删除用户')
        return super().get_queryset().exclude(is_deleted=True)

    def before_delete(self, *args, **kwargs):
        # 三元用户不能删除
        for username in BUILT_IN_USER_NAMES:
            if username == self.object.username:
                raise OperationNotAllowed('默认管理员不允许删除')

        # 有资源用户不能删除
        if Resource.objects.filter(user=self.object).exists():
            raise OperationNotAllowed('拥有资源的用户不允许删除')


class UserUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    更新用户
    """
    model = User
    pk_url_kwarg = 'user_id'
    form_class = UserUpdateForm
    permission_required = 'base.update_user'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.is_deleted:
            raise User.DoesNotExist(
                "未查询到用户: %s" %
                self.model._meta.object_name
            )
        # opt_log
        self.opt_logger.info(User.objects.get(pk=self.kwargs.get('user_id')), content='更新用户',
                             action='更新用户')
        return obj


class UserRoleUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    更新用户角色
    """
    model = User
    pk_url_kwarg = 'user_id'
    form_class = UserRoleUpdateForm
    permission_required = 'base.update_user_roles'

    def post(self, request, *args, **kwargs):
        # opt_log
        user = User.objects.get(pk=kwargs.get('user_id'))
        self.request.opt_obj = self.opt_logger.info(user, content='更新用户角色', remarks='更新用户角色')
        return super().post(request, *args, **kwargs)


class SetPassword(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    重新设置用户的密码（无需旧密码）
    """
    model = User
    form_class = SetPasswordForm
    http_method_names = ['put']
    permission_required = 'base.reset_password'

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.cleaned_data['user'])
        # send password update signal
        password_update_end.send(user=form.cleaned_data['user'], sender=self)

        # opt_log
        self.opt_logger.info(form.cleaned_data['user'], content='重置用户密码', remarks='重置用户密码')
        return self.render_to_json_response()


class ChangePassword(FormView):
    """
    用户更改密码，需要验证旧密码
    可选参数user，如果不传值则默认为当前登录用户（未登录又没有传user无法修改）
    每个用户都可以修改自己的密码，不需要权限
    """
    form_class = ChangePasswordForm
    http_method_names = ['put']

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.save()
        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.cleaned_data['user'])
        # send password update signal
        password_update_end.send(user=form.cleaned_data['user'], sender=self)
        # opt_log
        self.opt_logger.info(form.cleaned_data['user'], content='用户更改密码', remarks='用户更改密码')
        return self.render_to_json_response()

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.request_user = self.request.user
        return form


class AddressControlList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    地址控制列表
    """
    model = AddressControl
    permission_required = 'base.list_address_control'


class AddressControlCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    地址控制创建
    """
    model = AddressControl
    form_class = AddressControlForm
    permission_required = 'base.change_address_control'

    def form_valid(self, form):
        return super().form_valid(form)


class LoginPeriodDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    用户登录时段详情
    """
    model = User
    pk_url_kwarg = 'user_id'
    permission_required = 'base.view_login_period'

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)
        try:
            period = self.object.login_period
        except Exception as e:
            # prevent from DoesNotExist exception
            if e.__class__.__name__ == 'RelatedObjectDoesNotExist':
                period = LoginPeriod.objects.create(user=self.object)
            else:
                raise
        return period


class LoginPeriodUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    用户登录时段更新
    """
    model = LoginPeriod
    form_class = LoginPeriodUpdateForm
    permission_required = 'base.change_login_period'


class AddressControlDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    ip/mac 地址控制删除
    """
    model = AddressControl
    permission_required = 'base.delete_address_control'

    def get_queryset(self):
        # opt_log
        address_control = AddressControl.objects.get(pk=self.kwargs.get('pk'))
        self.opt_logger.info(address_control, content='ip/mac 地址控制删除', remarks='删除 %s 的地址控制<ip:%s,mac:%s>'
                                                                               % (address_control.user.username,
                                                                                  address_control.ip,
                                                                                  address_control.mac))
        return super().get_queryset()


class LoginLimitDetail(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """
    用户登录限制详情
    """
    model = User
    pk_url_kwarg = 'user_id'
    related_sets = ('address_control', 'login_terminal',)
    many_to_many_fields = ('login_period',)
    permission_required = ['base.list_address_control', 'base.list_login_terminal', 'base.view_login_period']

    def get(self, request, *args, **kwargs):
        data = model_to_dict(self.get_object(), fields=('is_enabled_address_control',), related_sets=self.related_sets,
                             many_to_many_fields=self.many_to_many_fields)
        return self.render_to_json_response(data=data)


class LoginLimitEdit(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """
    用户登录限制编辑
    """

    form_class = LoginLimitEditForm
    permission_required = ['base.change_address_control', 'base.delete_address_control',
                           'base.change_login_terminal', 'base.change_login_period', ]

    def form_valid(self, form):
        data = form.cleaned_data
        user = User.objects.filter(pk=form.cleaned_data.get('user_id')).first()
        address_control_list = data.get('address_control_list')
        login_period = data.get('login_period')
        login_terminal = data.get('login_terminal')
        # ip && mac
        for address in address_control_list.get('address_control'):
            AddressControl.objects.update_or_create(address, user=user)
        # 登录时段
        LoginPeriod.objects.update_or_create(login_period, user=user)
        # 物理地址
        LoginTerminal.objects.update_or_create(login_terminal, user=user)
        User.objects.update(is_enabled_address_control=address_control_list.get('is_enabled'))
        # opt_log
        self.opt_logger.info(user, content='用户登录限制编辑', remarks='用户登录限制编辑')
        return self.render_to_json_response(data=data)
