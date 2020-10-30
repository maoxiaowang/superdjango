from gettext import gettext

from django.apps import apps
from django.views.generic.detail import SingleObjectMixin

from base.constants import BUILT_IN_USER_IDS, USER_SYS_ID, SUB_SYS_ROLE_EXCLUDING_PERMS, GET_APP_LABEL_NAME
from base.forms.role import *
from base.management.commands.init_roles import ECLOUD_APP_LIST
from base.models.role import Group as Role
from common.core.exceptions import OperationNotAllowed
from common.forms import model_to_dict
from common.mixin import LoginRequiredMixin, PermissionRequiredMixin
from common.views import CreateView, AdvancedListView, UpdateView, DeleteView


class RoleList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    角色列表
    """
    model = Role
    permission_required = 'auth.list_role'
    many_to_many_fields = ('user_set',)

    def handle_queryset(self, queryset, **kwargs):
        roles = list()
        for role in queryset:
            role_dict = model_to_dict(role)
            role_dict.update({'number_of_users': role.user_set.count()})
            roles.append(role_dict)
        return roles


class RoleCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    角色创建
    """
    model = Role
    form_class = RoleCreateForm
    permission_required = 'auth.create_role'

    def form_valid(self, form):
        response = super().form_valid(form)
        # add perms to group
        self.object.permissions.add(*form.cleaned_data['perms'])
        # opt_log
        self.opt_logger.info(form.cleaned_data['name'], content='创建角色', remarks='创建角色', model=Role)
        return response


class RoleUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    角色更新
    """
    model = Role
    form_class = RoleUpdateForm
    pk_url_kwarg = 'role_id'
    permission_required = 'auth.update_role'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # opt_log
        self.opt_logger.info(obj, content='角色更新', remarks='角色更新')
        return obj


class RoleDelete(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    角色删除
    """
    model = Role
    pk_url_kwarg = 'role_id'
    permission_required = 'auth.delete_role'

    def before_delete(self, *args, **kwargs):
        if self.object.id in BUILT_IN_USER_IDS:
            raise OperationNotAllowed
            # opt_log
        self.opt_logger.info(Role.objects.get(pk=self.kwargs.get('role_id')).name, content='删除角色', remarks='删除角色',
                             model=Role)


class RoleUsersList(LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin,
                    AdvancedListView):
    """
    角色下的用户列表
    """
    model = Role
    pk_url_kwarg = 'role_id'
    permission_required = 'auth.list_role_users'

    def handle_queryset(self, queryset, **kwargs):
        role = self.get_object(queryset)
        return role.user_set.all()


class RoleUsersAdd(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    向角色中添加用户
    """
    model = Role
    pk_url_kwarg = 'role_id'
    form_class = RoleUsersAddForm
    permission_required = 'auth.add_role_users'

    def form_valid(self, form):
        if self.request.user.id != USER_SYS_ID:
            raise OperationNotAllowed('仅允许默认系统管理员分配用户')
            # opt_log
        self.opt_logger.info(self.request.user, content='向角色中添加用户', remarks='向角色中添加用户',
                             model=Role)
        return super().form_valid(form)


class RoleUsersRemove(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    从角色中移除用户
    """
    model = Role
    pk_url_kwarg = 'role_id'
    form_class = RoleUsersRemoveForm
    permission_required = 'auth.remove_role_users'


# class RolePermsAdd(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     向角色中添加权限
#     """
#     model = Role
#     pk_url_kwarg = 'role_id'
#     form_class = RolePermsAddForm
#     permission_required = 'base.add_role_perms'
#
#
# class RolePermsRemove(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     """
#     从角色中移除权限
#     """
#     model = Role
#     pk_url_kwarg = 'role_id'
#     form_class = RolePermsRemoveForm
#     permission_required = 'base.remove_role_perms'


class RolePermsList(LoginRequiredMixin, PermissionRequiredMixin, SingleObjectMixin,
                    AdvancedListView):
    """
    角色下的权限列表

    返回值中 available_for_sub_sys 表示该权限对于子系统管理员是否可用
    """
    model = Role
    pk_url_kwarg = 'role_id'
    permission_required = 'auth.list_role_perms'

    def get_queryset(self):
        self.queryset = self.model.objects.prefetch_related('permissions__content_type')
        return super().get_queryset()

    def handle_queryset(self, queryset, **kwargs):
        result = list()
        perm_ids = list()
        role = self.get_object(queryset)
        perms = role.permissions.values(
            'id', 'name', 'codename', 'content_type__app_label', 'content_type__model',
        )

        for perm in perms:
            if perm['id'] not in perm_ids:
                app_label = perm['content_type__app_label']
                model_name = perm['content_type__model']
                perm_str = '%s.%s' % (app_label, perm['codename'])
                available = True if perm_str not in SUB_SYS_ROLE_EXCLUDING_PERMS else False
                model = apps.get_model(app_label, model_name)
                # _for_sub_sys_admin
                result.append({
                    'id': perm['id'],
                    'name': gettext(perm['name']),
                    # 'content_type': perm.content_type.id,
                    'codename': perm['codename'],
                    'app_label': app_label,
                    'app_label_local': GET_APP_LABEL_NAME(app_label).name,
                    # 'app_label_local': gettext(app_label),
                    'model': model_name,
                    # 'model_local': gettext(model_name),
                    'model_local': model._meta.verbose_name_plural,
                    'available_for_sub_sys': available
                })
                perm_ids.append(perm['id'])
        if bool(self.request.GET.get('parm')):
            results = list()
            for results_codename in result:
                if '%s.%s' % (
                        results_codename.get('app_label'),
                        results_codename.get('codename')) not in SUB_SYS_ROLE_EXCLUDING_PERMS:
                    results.append(results_codename)
            return results
        return result
