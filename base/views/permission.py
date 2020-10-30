from django.apps import apps
from django.utils.translation import gettext

from base.models import Permission, Resource
from common.core.cache import GenericBasedCache
from common.forms import Serializer
from common.mixin import LoginRequiredMixin, PermissionRequiredMixin
from common.views.general import (AdvancedListView)

User = apps.get_model('base.User')


class UserPermsCache(GenericBasedCache):

    def __init__(self, name: str, user_id, **kwargs):
        super().__init__(name, **kwargs)
        self.name += str(user_id)


class PermissionsList(LoginRequiredMixin, PermissionRequiredMixin, AdvancedListView):
    """
    权限列表，包括所有及特定某用户的权限
    URL参数：user_id
    """
    model = Permission
    many_to_many_fields = ('content_type',)
    permission_required = 'auth.list_permission'

    def get_queryset(self):
        self.queryset = self.model.objects.prefetch_related('content_type')
        return super().get_queryset()

    @staticmethod
    def _format_perms(perms):
        perm_ids = list()
        result = list()
        for perm in perms:
            if perm['id'] not in perm_ids:
                result.append({
                    'id': perm['id'],
                    'name': perm['name'],
                    # 'content_type': perm.content_type.id,
                    'codename': perm['codename'],
                    'app_label': perm['content_type']['app_label'],
                    'app_label_local': gettext(perm['content_type']['app_label']),
                    'model': perm['content_type']['model'],
                    'model_local': gettext(perm['content_type']['model'])
                })
                perm_ids.append(perm['id'])
        return result

    def handle_queryset(self, queryset, **kwargs):
        user_id = self.request.GET.get('user_id')
        m2m_fields = self.many_to_many_fields

        perms = Serializer(
            queryset, many_to_many_fields=m2m_fields).to_python()
        if user_id:
            assert user_id.isdigit()
            user = User.objects.get(id=user_id)
            if user.is_superuser:
                return self._format_perms(perms)

            roles = user.groups.prefetch_related('permissions')

            def unite_perms(a_perms=None, i=0):
                if a_perms is None:
                    # first
                    a_perms = Serializer(
                        roles[0].permissions.all(),
                        many_to_many_fields=m2m_fields).to_python()
                    i += 1
                try:
                    b_perms = Serializer(
                        roles[i].permissions.all(),
                        many_to_many_fields=m2m_fields).to_python()
                except IndexError:
                    return a_perms

                a_perms.extend(b_perms)
                return unite_perms(a_perms=a_perms, i=i + 1)

            union_perms = unite_perms()
            # remove dup
            pks = list()
            perms = list()
            for perm in union_perms:
                if perm['id'] not in pks:
                    perms.append(perm)
                    pks.append(perm['id'])

        return self._format_perms(perms)


