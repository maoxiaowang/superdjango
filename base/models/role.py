from django.contrib.auth.models import Group as _Group
from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = [
    'Group'
]

if not hasattr(_Group, 'description'):
    description = models.CharField(_('Description'), max_length=255, blank=True)
    description.contribute_to_class(_Group, 'description')
if not hasattr(_Group, 'created_at'):
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    created_at.contribute_to_class(_Group, 'created_at')


class Group(_Group):
    """
    Roles
    """
    class Meta:
        proxy = True
        default_permissions = ()
        ordering = ('id',)
        permissions = (
            ('view_role', _('Can view role')),
            ('create_role', _('Can create role')),
            ('update_role', _('Can update role')),
            ('delete_role', _('Can delete role')),
        )

    def __str__(self):
        return '%s (%s)' % (self.name, self.pk)

    def natural_key(self):
        return {
            'id': self.pk,
            'name': self.name,
            'description': self.description
        }
