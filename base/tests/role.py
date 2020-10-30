import json

from django.test import TestCase
from django.urls import reverse

from base.models import Group as Role, Permission
from common.test import TestMixin


class RoleModelTests(TestMixin, TestCase):
    ...


class RoleViewBaseTests(TestMixin, TestCase):

    def test_role_list(self):
        """
        角色列表
        """
        self.login_as_superuser()
        role = self._create_role()
        response = self.client.get(reverse('base:role_list'))
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])
        self.assertEqual(content['data']['total_length'], 1)
        self.assertEqual(content['data']['objects'][0]['name'], role.name)

    def test_role_create(self):
        """
        创建子角色
        """
        self.login_as_superuser()
        role = self.init_roles().first()
        self.settings(DEBUG=True)
        perm = Permission.objects.last()
        role.permissions.add(perm.id)
        data = {
            'name': 'test_role',
            'description': 'test description',
            'parent_id': 1,
            'perms': '[%d]' % perm.id
        }
        response = self.client.post(reverse('base:role_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])

    def test_role_update(self):
        """
        更新子角色，并更新权限
        """
        self.login_as_superuser()
        role = self.init_roles().first()
        perms = Permission.objects.order_by('-id')
        perms = list(perms[(perms.count()-5):].values_list('id', flat=True))  # 取最后5个权限
        role.permissions.add(*perms)  # 添加到父角色中
        sub_role = self._create_role()
        new_desc = 'test description'
        new_name = 'new_role_name'
        new_perms = perms[2:]
        data = {
            'name': new_name,
            'description': new_desc,
            'parent_id': 1,
            'perms': str(new_perms)
        }
        response = self.client.post(reverse('base:role_update', args=(sub_role.id,)), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['data']['description'], new_desc)
        self.assertEqual(content['data']['name'], new_name)

        # assert perms
        self.assertEqual(sub_role.permissions.count(), len(new_perms), '添加了三个权限')

    def test_role_delete(self):
        """
        删除子角色
        """
        self.init_roles()
        self.login_as_superuser()
        role = self._create_role()
        response = self.client.delete(reverse('base:role_delete', args=(role.id,)))
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])

    def test_role_add_and_remove_users(self):
        """
        给角色下添加/移除用户
        """
        self.init_roles()
        self.login_as_superuser()
        role = self._create_role()
        user1 = self._create_user()
        user2 = self._create_user()

        data = {
            'users': str([user1.id, user2.id])
        }
        # add users
        response = self.client.post(reverse('base:role_users_add', args=(role.id,)), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])
        self.assertEqual(role.user_set.count(), 2, '添加了两个用户')

        # remove users
        response = self.client.post(reverse('base:role_users_remove', args=(role.id,)), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])
        self.assertEqual(role.user_set.count(), 0, '移除掉添加的两个用户')


class RoleViewFeatureTests(TestMixin, TestCase):

    def test_role_delete_except_for_builtins(self):
        """
        不能删除内置角色
        """
        self.login_as_superuser()
        roles = self.init_roles()
        for role in roles:
            response = self.client.delete(reverse('base:role_delete', args=(role.id,)))
            content = json.loads(response.content)
            self.assertEqual(content['code'], 409)
            self.assertFalse(content['result'])

    def test_builtin_roles_cannot_be_editing(self):
        """
        不能编辑内置角色
        """
        self.login_as_superuser()
        roles = self.init_roles()
        for role in roles:
            data = {
                'perms': '[1,2]',
                'name': role.name,
            }
            response = self.client.post(reverse('base:role_update', args=(role.id,)), data=data)
            content = json.loads(response.content)
            self.assertEqual(content['code'], 400)
            self.assertFalse(content['result'])

    def test_sub_role_perms_less_or_equal_than_parents_creating(self):
        """
        创建角色时，子角色权限不能大于父角色权限
        """
        self.login_as_superuser()
        sys_role = self.init_roles().first()
        perms = Permission.objects.filter(id__lte=20).values_list('id', flat=True)
        sys_role.permissions.add(*list(perms))
        data = {
            'name': 'sub_role',
            'parent_id': 1,
            'perms': '[19, 20, 21]'  # 父角色没有21权限
        }
        response = self.client.post(reverse('base:role_create'), data=data)
        content = json.loads(response.content)
        self.assertTrue(content['code'], 400)
        self.assertFalse(content['result'])

    def test_sub_role_perms_less_or_equal_than_parents_updating(self):
        """
        更新角色时，子角色权限不能大于父角色权限
        """
        self.login_as_superuser()
        sys_role = self.init_roles().first()
        perms = Permission.objects.filter(id__lte=20).values_list('id', flat=True)
        sys_role.permissions.add(*list(perms))
        data = {
            'name': 'sub_role',
            'parent_id': 1,
            'perms': '[19, 20, 21]'  # 父角色没有21权限
        }
        response = self.client.post(reverse('base:role_update', args=(sys_role.id,)), data=data)
        content = json.loads(response.content)
        self.assertTrue(content['code'], 400)
        self.assertFalse(content['result'])
