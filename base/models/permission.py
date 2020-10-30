from django.contrib.auth.models import Permission as _Permission
from django.utils.translation import ugettext_lazy as _, gettext

__all__ = [
    'Permission'
]


class Permission(_Permission):
    class Meta:
        proxy = True
        default_permissions = ()
        permissions = (
            ('view_permission', _('Can view permission')),
        )

    def natural_key(self):
        return {'id': self.pk, 'name': gettext(self.name),
                'content_type_name': gettext(self.content_type.name),
                'content_type_id': self.content_type.id,
                'codename': self.codename}
