from django import forms
from django.utils.translation import ugettext_lazy as _

from base.constants import BUILT_IN_ROLE_IDS, BUILT_IN_USER_IDS, ROLE_SYS_ID, SUB_SYS_ROLE_EXCLUDING_PERMS
from base.models import Group as Role, User, Permission
from common.core.validators import IntListValidator
from common.forms import FormMixin
from common.forms.fields import ListField

__all__ = [
    'RoleCreateForm',
    'RoleUpdateForm',
    'RoleUsersAddForm',
    'RoleUsersRemoveForm',
    # 'RolePermsAddForm',
    # 'RolePermsRemoveForm'
]


class RoleCreateForm(FormMixin, forms.ModelForm):
    field_order = ('parent_id', 'perms')

    perms = ListField(label='权限', validators=[IntListValidator()])

    class Meta:
        model = Role
        fields = ('name', 'description', 'parent_id')

    def clean_parent_id(self):
        parent_id = self.cleaned_data['parent_id']
        if parent_id != ROLE_SYS_ID:
            # 仅允许默认系统管理员有子角色
            self.add_error(
                'parent_id',
                forms.ValidationError(
                    '仅允许默认系统管理员创建子角色',
                    code='parent_not_valid'
                )
            )
        return parent_id

    def clean_perms(self):
        perms = self.cleaned_data['perms']
        parent_id = self.cleaned_data['parent_id']
        parent_role = Role.objects.get(id=parent_id)
        available_perms = parent_role.permissions

        if parent_id > 0:  # ROLE_SYS_ID
            # 对于子角色，过滤掉特殊权限
            excluding_perms = list()
            for item in SUB_SYS_ROLE_EXCLUDING_PERMS:
                app_label, codename = item.split('.')
                try:
                    perm = Permission.objects.get(codename=codename, content_type__app_label=app_label)
                except Permission.DoesNotExist:
                    continue
                excluding_perms.append(perm.id)
            available_perms = available_perms.exclude(id__in=excluding_perms)
        perm_id_list = available_perms.values_list('id', flat=True)

        illegal_perms = list()
        for perm in perms:
            if perm not in perm_id_list:
                illegal_perms.append(perm)
        if illegal_perms:
            self.add_error(
                'perms',
                forms.ValidationError(
                    _("不可用的权限'%(perm_ids)s'。子角色仅能继承其父角色拥有的权限。"),
                    params={'perm_ids': ', '.join(map(lambda x: str(x), illegal_perms))}
                )
            )
        return perms


class RoleUpdateForm(FormMixin, forms.ModelForm):
    perms = ListField(label='权限', validators=[IntListValidator()])

    class Meta:
        model = Role
        fields = ('name', 'description')

    def clean_perms(self):
        perms = self.cleaned_data['perms']
        all_perms = Permission.objects.filter(id__in=perms).values_list('id', flat=True)
        diff_perms = list(map(lambda x: str(x), filter(lambda u: u not in all_perms, perms)))
        if diff_perms:
            self.add_error(
                'perms',
                forms.ValidationError(
                    '权限ID为%(perms)s的权限不存在。',
                    params={'perms': ', '.join(diff_perms)},
                    code='perm_not_exist'
                )
            )
        return perms

    def _post_clean(self):
        super()._post_clean()
        if self.instance.id in BUILT_IN_ROLE_IDS:
            self.add_error(
                None,
                forms.ValidationError(
                    '默认管理员不允许变更权限。',
                    code='default_manager'
                )
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)
        old = instance.permissions.all().values_list('id', flat=True)
        new = self.cleaned_data['perms']
        add = list(filter(lambda x: x not in old, new))
        delete = list(filter(lambda x: x not in new, old))
        instance.permissions.add(*add)
        instance.permissions.remove(*delete)
        return instance


# class RoleUsersUpdateForm(FormMixin, forms.ModelForm):
#     users = ListField(validators=[IntListValidator()])
#
#     class Meta:
#         model = Role
#         fields = ()
#
#     def clean_users(self):
#         users = self.cleaned_data['users']
#         exist_users = User.objects.filter(id__in=users).values_list('id', flat=True)
#         diff_users = map(lambda x: str(x), filter(lambda u: u not in exist_users, users))
#         if diff_users:
#             for user in diff_users:
#                 self.add_error(
#                     'users',
#                     forms.ValidationError(
#                         _('User with id %(id)s not exists.'),
#                         params={'id': user}
#                     )
#                 )
#         return users
#
#     def save(self, commit=True):
#         super().save(commit=commit)
#         role_users = self.instance.user_set
#         role_users.clear()
#         role_users.add(*self.cleaned_data['users'])


class RoleUsersAddForm(FormMixin, forms.ModelForm):
    users = ListField(validators=[IntListValidator()])

    class Meta:
        model = Role
        fields = ()

    def _post_clean(self):
        if self.instance.is_default_manager:
            self.add_error(None, forms.ValidationError(
                '不能给默认管理员角色分配用户。', code='invalid_role'))
        super()._post_clean()

    def clean_users(self):
        users = self.cleaned_data['users']
        valid_users = User.objects.filter(id__in=users).values_list('id', flat=True)
        # 不存在的用户
        non_exist_users = map(lambda x: str(x), filter(lambda u: u not in valid_users, users))
        for user in non_exist_users:
            self.add_error(
                'users',
                forms.ValidationError(
                    '用户ID为%(id)s的用户不存在。',
                    params={'id': user},
                    code='user_no_exist'
                )
            )
        # 默认三员，不允许更改角色
        for user in valid_users:
            if user in BUILT_IN_USER_IDS:
                self.add_error(
                    'users',
                    forms.ValidationError(
                        "默认管理员不允许变更角色。",
                        code='default_manager'
                    )
                )
        return users

    def save(self, commit=True):
        instance = super().save(commit=commit)
        instance.user_set.add(*self.cleaned_data['users'])
        return instance


class RoleUsersRemoveForm(RoleUsersAddForm):

    def save(self, commit=True):
        instance = super().save(commit=commit)
        instance.user_set.remove(*self.cleaned_data['users'])
        return instance

# class RolePermsAddForm(FormMixin, forms.ModelForm):
#     perms = ListField(validators=[IntListValidator()])
#
#     class Meta:
#         model = Role
#         fields = ()
#
#     def clean_perms(self):
#         perms = self.cleaned_data['perms']
#         exist_perms = Permission.objects.filter(id__in=perms).values_list('id', flat=True)
#         diff_perms = map(lambda x: str(x), filter(lambda u: u not in exist_perms, perms))
#         if diff_perms:
#             for perm in diff_perms:
#                 self.add_error(
#                     'users',
#                     forms.ValidationError(
#                         _('Permission with id %(id)s not exists.'),
#                         params={'id': perm}
#                     )
#                 )
#         return perms
#
#     def save(self, commit=True):
#         self.instance.permissions.add(*self.cleaned_data['perms'])
#
#
# class RolePermsRemoveForm(RolePermsAddForm):
#
#     def save(self, commit=True):
#         self.instance.permissions.remove(*self.cleaned_data['perms'])
