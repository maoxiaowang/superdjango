from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()
Role = apps.get_model('base.Group')


class TestMixin:
    """
    Inherit this mixin to your tests view
    """
    superuser = 'admin'
    password = 'PAss2w0rd!@#'
    role = 'role'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = User
        self.role_model = Role

    @property
    def username(self):
        return get_random_string()

    @property
    def email(self):
        return get_random_string() + '@example.com'

    def _get_user(self, **kwargs):
        return self.user_model.objects.get(**kwargs)

    def _delete_user(self, username):
        self.user_model.objects.get(username=username).delete()

    def _create_user(self, username=None, password=None, email=None, **extra_fields):
        """
        如果没有传参，则创建默认测试用户
        """
        return self.user_model.objects.create_user(
            username or self.username,
            email or self.email,
            password or self.password,
            **extra_fields
        )

    def _create_superuser(self, username, password, email=None, **extra_fields):
        return self.user_model.objects.create_superuser(
            username, email or self.email, password, **extra_fields
        )

    def _add_user_role(self, user, role_name):
        user.groups.add(self.role_model.objects.get(role_name))

    def login_as_superuser(self, **extra_fields):
        """
        新建超级用户
        """
        extra_fields.setdefault('is_active', True)
        superuser = self._create_superuser(self.superuser, self.password, **extra_fields)
        self.client.login(username=self.superuser, password=self.password)
        return superuser

    def login_as_user(self):
        user = self._create_user()
        self.client.login(username=user.username, password=self.password)
        return user

    def _create_role(self, name=None, parent_id=1):
        return Role.objects.create(name=name or self.role, parent_id=parent_id)
