import json

from django.contrib.auth.hashers import make_password
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse

from common.test import TestMixin


class UserModelTests(TestMixin, TestCase):

    def test_user_is_inactive(self):
        """
        初始用户应该为未激活状态
        """
        user = self.login_as_user()
        self.assertFalse(user.is_active)

    def test_user_is_unlock(self):
        """
        初始用户应该非锁定状态
        """
        user = self.login_as_user()
        self.assertFalse(user.is_locked)

    def test_user_username_is_unique(self):
        """
        用户名唯一
        """
        user = self._create_user()
        with self.assertRaises(IntegrityError):
            self._create_user(username=user.username)

    def test_user_email_is_required(self):
        """
        邮箱唯一
        """
        password = make_password(self.password)
        user = self.user_model.objects.create(
            username=self.username,
            password=password,
        )
        with self.assertRaisesRegex(IntegrityError, r'1062.*Duplicate entry.*'):
            self.user_model.objects.create(
                username=user.username,
                password=password,
            )


class UserViewTests(TestMixin, TestCase):

    def test_user_create(self):
        """
        普通用户创建
        """
        self.login_as_superuser()

        data = {
            'username': self.username,
            'password1': self.password,
            'password2': self.password,
            'email': self.email
        }
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertTrue(content['result'])

    def test_user_create_password_strength(self):
        """
        用户创建，密码强度测试
        """
        self.login_as_superuser()
        week_password = 'password'
        strong_password = self.password
        data = {
            'username': self.username,
            'password1': week_password,
            'password2': week_password,
            'email': self.email
        }
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 400)
        self.assertFalse(content['result'])  # 密码强度弱

        data['password1'] = data['password2'] = 'ad2#@!'
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 400)
        self.assertFalse(content['result'])  # 密码长度不够

        data['password1'] = 'mismatch' + strong_password
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['code'], 400)
        self.assertFalse(content['result'])  # 强度足够，但两次密码不等

    def test_user_create_username_is_required(self):
        """
        用户创建，用户名是必填项
        """
        data = {
            # 'username': self.username,
            'password1': self.password,
            'password2': self.password,
            'email': self.email
        }
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertFalse(content['result'])

    def test_user_create_display_name_is_optional(self):
        """
        创建用户时，display_name可选
        """
        self.login_as_superuser()
        display_name = 'my display name'
        data = {
            'username': self.username + '1',
            'password1': self.password,
            'password2': self.password,
            'email': self.email,
        }
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['data']['display_name'], '')

        data['username'] = self.username
        data['email'] = self.email
        data['display_name'] = display_name
        response = self.client.post(reverse('base:user_create'), data=data)
        content = json.loads(response.content)
        self.assertEqual(content['data']['display_name'], display_name)

    def test_user_update(self):
        """
        更新用户时，用户名不可改
        """
        self.login_as_superuser()

        user = self._create_user()
        new_display_name = 'new_display_name'
        data = {
            'email': self.email,
            'username': 'new_name',
            'display_name': new_display_name
        }
        response = self.client.post(reverse('base:user_update', args=(user.id,)), data=data)
        content = json.loads(response.content)
        self.assertTrue(content['result'])
        self.assertEqual(content['data']['username'], user.username)  # 用户名不可更改
        self.assertEqual(content['data']['display_name'], new_display_name)

    def test_user_delete(self):
        """
        用户删除
        """
        self.login_as_superuser()

        # case one, user is not active, will be deleted from database
        user = self._create_user()
        response = self.client.delete(reverse('base:user_delete', args=(user.id,)))
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertEqual(content['result'], True)
        self.assertFalse(user.is_active)
        with self.assertRaises(self.user_model.DoesNotExist):
            self._get_user(id=user.id)

        # case two, user is active, so just set deleted to True
        user = self._create_user(is_active=True)
        response = self.client.delete(reverse('base:user_delete', args=(user.id,)))
        content = json.loads(response.content)
        self.assertEqual(content['code'], 200)
        self.assertEqual(content['result'], True)
        user = self._get_user(id=user.id)  # 并没有删除，不会出现异常
        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)

    def test_user_list(self):
        """
        用户列表测试
        """
        self.login_as_superuser()

        self._create_user(self.username, self.password, email=self.email)
        self._create_user(self.username, self.password, email=self.email)

        # 请求接口
        response = self.client.get(reverse('base:user_list'))
        content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)  # response代码
        self.assertEqual(content['code'], 200)  # 接口代码
        self.assertTrue(content['result'])  # 接口是否成功
        self.assertEqual(content['data']['total_length'], 3)
        self.assertEqual(len(content['data']['objects']), 3)
