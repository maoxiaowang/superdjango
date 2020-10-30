import os

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.contrib.sessions.models import Session
from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Q, CharField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from common.core.validators import MACAddressValidator, SymbolChineseNameValidator
from common.models.fields import ListField, IPField, MACField


def relative_avatar_path(instance, filename):
    return os.path.join('users', str(instance.id), 'avatars', filename)


class CustomBaseUserManager(BaseUserManager):

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing the domain part of it.
        """
        email = email or ''
        try:
            email_name, domain_part = email.strip().rsplit('@', 1)
        except ValueError:
            pass
        else:
            email = email_name + '@' + domain_part.lower()
        return email


class UserManager(CustomBaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        self.model = get_user_model()
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        # extra_fields.setdefault('id', UUID.uuid4)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

    @staticmethod
    def get_user_dir(user_id):
        return os.path.join(django_settings.MEDIA_ROOT, 'users', str(user_id))


class User(AbstractUser):
    """
    Custom user model
    """
    groups = models.ManyToManyField(
        'Group')
    user_permissions = models.ManyToManyField(
        Permission)
    username = models.CharField(
        _('username'),
        max_length=32,
        unique=True,
        help_text=_(
            'Required. 32 characters or fewer. '
            'Letters, digits and @/./+/-/_ only.'),
        validators=[ASCIIUsernameValidator()],
        error_messages={
            _("A user with that username already exists."),
        },
    )
    display_name = models.CharField(
        _('display name'),
        max_length=150,
        validators=[SymbolChineseNameValidator()],
        blank=True,
        help_text=_('This name is only used to display.')
    )
    email = models.EmailField(_('email'), max_length=255, unique=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    avatar = models.ImageField(
        _('avatar'), storage=default_storage, default='default/avatars/user/default.png',
        upload_to=relative_avatar_path, blank=True
    )
    password_updated_at = models.DateTimeField(_('password updated at'), null=True, default=None)
    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'auth_user'
        ordering = ('id',)
        default_permissions = ()
        permissions = (
            ('view_user', _('Can view user')),
            ('create_user', _('Can create user')),
            ('update_user', _('Can update user')),
            ('delete_user', _('Can delete user')),
            ('reset_password', _('Can reset password')),
        )

    def __str__(self):
        return '%s (%d)' % (self.username, self.id)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    @property
    def home_path(self):
        return os.path.join(django_settings.MEDIA_ROOT, 'users', str(self.id))

    @property
    def avatar_path(self):
        return os.path.join(self.home_path, 'avatars')

    def natural_key(self):
        return {'id': self.id, 'username': self.username, 'avatar': self.avatar.url}

    @property
    def get_display_name(self):
        return self.display_name or self.username
