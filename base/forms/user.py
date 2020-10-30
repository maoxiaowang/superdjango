from django import forms
from django.contrib.auth import password_validation, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.files.uploadedfile import InMemoryUploadedFile

from common.core.cache import queryset_cache
from common.core.settings import parser, conf_path, sys_settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from base.constants import BUILT_IN_ROLE_IDS
from base.helpers.user import address_is_permitted, access_period_is_permitted
from base.models import User, LoginPeriod, AddressControl, Group as Role
from base.models.user import LoginTerminal
from common.core.settings import db_settings
from common.core.validators import MACAddressValidator
from common.forms import ModelForm, FormMixin, Form
from common.forms.fields import DictField, ListField
from common.utils.avatar import process_user_avatar
from common.utils.crypto import AESCrypt
from common.utils.request import get_remote_ip_address
from common.log import default_logger as logger
from common.core.settings import sys_settings


class UserLoginForm(AuthenticationForm):
    mac = forms.CharField(label='客户端mac', required=False, validators=[MACAddressValidator()])
    terminal_uuid = forms.CharField(label='客户终端唯一标识', required=False)
    extra_messages = {
        'account_locked': "帐号被锁定，请联系管理员.",
        'ip_blocked': 'IP地址异常，请检查.',
        'ip_or_mac_blocked': 'IP地址或者MAC地址异常，请检查.',
        'mac_blocked': 'MAC地址异常，请检查',
        'login_terminal_blocked': '登录终端异常，请检查',
        'login_period_blocked': '登录时间段异常，请检查',
        'without_roles': '该用户尚未分配角色，无法登录。',
        'is_delete': '该帐号已被删除，无法登录'
    }
    keep_login = forms.BooleanField(label='保持登录', required=False)

    def __init__(self, request=None, *args, **kwargs):
        self.error_messages.update(self.extra_messages)
        super().__init__(request=request, *args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        password = self.decrypt_password(password)
        return password

    def decrypt_password(self, password):
        try:
            password = AESCrypt(sys_settings.default.aes_key).decrypt(password)
        except Exception as e:
            if sys_settings.default.debug:
                logger.warning("密码解密失败，以密文继续登录", e)
                pass
            else:
                raise self.get_invalid_login_error()
        return password

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        # password = self.decrypt_password(password)

        if username is not None and password:
            # authentication
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
                self.check_user_locking(self.user_cache)
                self.check_user_roles(self.user_cache)
                self.check_user_delete(self.user_cache)
                self.check_user_address(self.user_cache)
                self.check_user_terminal(self.user_cache)
                self.check_user_period(self.user_cache)

        return self.cleaned_data

    def check_user_locking(self, user):
        if user.is_locked:
            login_failed = user.login_failed
            past_seconds = (timezone.now() - login_failed.updated_at).seconds
            lock_seconds = db_settings.user_lock_minutes * 60
            if past_seconds > lock_seconds:
                user.is_locked = False
                user.save()
                login_failed.times = 0
                login_failed.save()
            raise forms.ValidationError(
                self.error_messages['account_locked'],
                code='account_locked',
            )

    def check_user_roles(self, user):
        """
        没有分配角色的用户不允许登录
        """
        # Just for development
        if user.username == 'admin':
            return
        if not user.groups.exists():
            raise forms.ValidationError(
                self.extra_messages['without_roles'],
                code='without_roles'
            )

    def check_user_delete(self, user):
        """
        检查用户是否删除
        """
        if user.is_deleted is True:
            raise forms.ValidationError(
                self.extra_messages['is_delete'],
                code='is_delete'
            )

    def check_user_address(self, user):
        """
        检查用户登录ip，mac限制
        """
        if bool(user.is_enabled_address_control):
            ip = get_remote_ip_address(self.request)
            # mac = get_remote_mac_address(self.request)
            mac = self.cleaned_data.get('mac')
            ip_allowed, mac_allowed = address_is_permitted(user, ip, mac)
            if not ip_allowed and not mac_allowed:
                raise forms.ValidationError(
                    self.extra_messages['ip_or_mac_blocked'],
                    code='ip_or_mac_blocked', params={'addr': ip}
                )
            if not ip_allowed:
                raise forms.ValidationError(
                    self.extra_messages['ip_blocked'],
                    code='ip_blocked', params={'addr': ip}
                )
            if not mac_allowed:
                raise forms.ValidationError(
                    self.extra_messages['mac_blocked'],
                    code='mac_blocked', params={'addr': mac}
                )

    def check_user_terminal(self, user):
        """
        检查用户登录终端UUID
        """
        terminal_obj = queryset_cache.base_LoginTerminal.filter(user=user).first()
        if terminal_obj is not None:
            if terminal_obj.is_enabled:
                terminal_uuid = self.cleaned_data.get('terminal_uuid')
                if terminal_obj.terminal_address != terminal_uuid:
                    raise forms.ValidationError(
                        self.extra_messages['login_terminal_blocked'],
                        code='login_terminal_blocked', params={'addr': terminal_uuid}
                    )

    def check_user_period(self, user):
        """
        检查用户登录时间
        """
        is_period = access_period_is_permitted(user)
        if is_period is False:
            raise forms.ValidationError(
                self.extra_messages['login_period_blocked'],
                code='login_period_blocked', params={'addr': None}
            )


class UserCreatForm(FormMixin, UserCreationForm):
    """
    Create user
    """

    class Meta:
        model = User
        fields = ('username', 'display_name', 'avatar')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if isinstance(avatar, InMemoryUploadedFile):
            # process and save avatar
            try:
                avatar = process_user_avatar(avatar)
            except Exception:
                raise forms.ValidationError(
                    _('Upload a valid image. The file you uploaded was '
                      'either not an image or a corrupted image.')
                )
        return avatar


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ('display_name', 'avatar')

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if isinstance(avatar, InMemoryUploadedFile):
            # process and save avatar
            try:
                avatar = process_user_avatar(avatar)
            except Exception:
                raise forms.ValidationError(
                    _('Upload a valid image. The file you uploaded was '
                      'either not an image or a corrupted image.')
                )
        return avatar

    def _post_clean(self):
        super()._post_clean()


class UserRoleUpdateForm(ModelForm):
    role_id = forms.IntegerField(required=False, label='角色ID')

    class Meta:
        model = User
        fields = ()

    def clean_role_id(self):
        role_id = self.cleaned_data.get('role_id')
        if role_id and not Role.objects.filter(id=role_id).exists():
            self.add_error(
                'role_id',
                forms.ValidationError(
                    '角色ID为%(role_id)s的角色不存在。',
                    params={'role_id': role_id},
                    code='role_no_exist'
                )
            )
        return role_id

    def _post_clean(self):
        super()._post_clean()
        # 默认三员，不允许更改角色
        if self.instance.id in BUILT_IN_ROLE_IDS:
            self.add_error(
                None,
                forms.ValidationError(
                    "默认管理员不允许变更角色。",
                    code='default_manager'
                )
            )

    def save(self, commit=True):
        self.instance.groups.clear()  # 只能存在一个角色
        role_id = self.cleaned_data.get('role_id')
        if role_id:
            self.instance.groups.add(role_id)


class SetPasswordForm(FormMixin, forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    user = forms.ModelChoiceField(
        User.objects,
        label=_('User'),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'autofocus': True,
            }
        )
    )
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_('New password confirmation'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        password1 = self.decrypt_password(password1)
        password2 = self.decrypt_password(password2)

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        validate_password(password2)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        # password = self.decrypt_password(password)

        user = self.cleaned_data['user']
        if user.is_deleted:
            raise User.DoesNotExist
        user.set_password(password)
        if commit:
            user.password_updated_at = timezone.now()
            user.save()
        return user

    def decrypt_password(self, password):
        try:
            password = AESCrypt(sys_settings.default.aes_key).decrypt(password)
        except Exception as e:
            if sys_settings.default.debug:
                logger.warning("密码解密失败，以密文继续登录", e)
                pass
            else:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return password


class ChangePasswordForm(FormMixin, forms.Form):
    """
    Allow users change their password
    """
    error_messages = {
        **SetPasswordForm.error_messages,
        'password_unchanged': _('New password can not be as same as the old one.'),
        'password_incorrect': _('Your old password was entered incorrectly. Please enter it again.'),
        'login_required': '需要登录'
    }

    user = forms.ModelChoiceField(
        User.objects,
        label='用户',
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'autofocus': True,
            }
        ),
        required=False
    )
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_('New password confirmation'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
    )
    old_password = forms.CharField(
        label=_('Old password'),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
            }
        ),
    )

    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if not self.request_user.is

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        password1 = self.decrypt_password(password1)
        password2 = self.decrypt_password(password2)

        validate_password(password2)
        user = self.request_user
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        old_password = self.cleaned_data.get('old_password')
        # extra validation - password can not be unchanged
        if old_password == password2:
            raise forms.ValidationError(
                self.error_messages['password_unchanged'],
                code='password_unchanged'
            )
        password_validation.validate_password(password2, user)
        return password2

    def clean_user(self):
        user = self.cleaned_data.get('user')
        if not user:
            user = self.request_user
            if not user.is_authenticated:
                raise forms.ValidationError(
                    self.error_messages['login_required'],
                    code='login_required'
                )
        return user

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        old_password = self.decrypt_password(old_password)

        user = self.cleaned_data['user']
        if not user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def decrypt_password(self, old_password):
        try:
            old_password = AESCrypt(sys_settings.default.aes_key).decrypt(old_password)
        except Exception as e:
            if sys_settings.default.debug:
                logger.warning("密码解密失败，以密文继续登录", e)
                pass
            else:
                raise forms.ValidationError(
                    self.error_messages['password_incorrect'],
                    code='password_incorrect',
                )
        return old_password

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        # password1 未解密 在此处需要解密
        password = self.decrypt_password(password)
        user = self.cleaned_data['user']
        if user.is_deleted:
            raise User.DoesNotExist
        user.set_password(password)
        if commit:
            user.password_updated_at = timezone.now()
            user.save()
        return user


class AddressControlForm(ModelForm):
    class Meta:
        model = AddressControl
        fields = '__all__'
        exclude = ('user',)

    def clean_mac(self):
        user = self.cleaned_data['user']
        mac = self.cleaned_data['mac']
        ip = self.cleaned_data['ip']
        # at least one, ip or mac
        if not any((mac, ip)):
            raise forms.ValidationError(
                _('IP set and MAC address must be fill at least one.'),
                code='ip_mac_all_empty'
            )

        # prevent from redundant items
        if AddressControl.objects.filter(user=user, ip=ip, mac=mac).exists():
            raise forms.ValidationError(
                _('Entry for user %(user)s with IP %(ip)s and MAC %(mac)s address exists.'),
                params={'ip': ip, 'mac': mac, 'user': user},
                code='entry_exists'
            )
        return mac


class LoginPeriodUpdateForm(ModelForm):

    def clean_end_time(self):
        end_time = self.cleaned_data['end_time']
        start_time = self.cleaned_data['start_time']
        if end_time < start_time:
            self.add_error(
                'end_time',
                forms.ValidationError(_('End time should be greater than start time.'))
            )
        return end_time

    class Meta:
        model = LoginPeriod
        fields = '__all__'
        exclude = ('user',)


class LoginTerminalForm(ModelForm):
    class Meta:
        model = LoginTerminal
        fields = '__all__'
        exclude = ('user',)


class LoginLimitEditForm(forms.Form):
    user_id = forms.IntegerField(label='user_id', required=True)
    address_control_list = DictField(label='地址控制<ip,mac>', required=False,
                                     help_text='{"is_enabled":false,'
                                               '"address_control":[{"ip":"1.0.0.0","mac":"00-FF-28-DF-3B-E2"}'
                                               ',{ "id":1,"ip": "1.0.0.0", "mac": "00-FF-59-9A-B7-23"}]}')
    login_period = DictField(label='登录时段', required=False,
                             help_text='{"weekdays":[1,2,3,4,5],"start_time":"12:00:00",'
                                       '"end_time":"23:59:59","is_enabled":false}')
    login_terminal = DictField(label='登录终端', required=False,
                               help_text='{"id":5, "terminal_address": "hhhhhh", "is_enabled": false }')

    def clean_login_period(self):
        login_period = self.cleaned_data['login_period']
        if not bool(login_period.get('end_time')):
            login_period['end_time'] = None
        if not bool(login_period.get('start_time')):
            login_period['start_time'] = None
        if login_period.get('is_enabled'):
            if not bool(login_period.get('end_time')):
                raise forms.ValidationError('请选择结束时间')
            if not bool(login_period.get('start_time')):
                raise forms.ValidationError('请选择开始时间')
            end_time = login_period.get('end_time')
            start_time = login_period.get('start_time')
            if end_time < start_time:
                self.add_error(
                    'end_time',
                    forms.ValidationError(_('结束时间应该大于开始时间'))
                )
        return login_period

    def clean_address_control_list(self):
        address_control_list = self.cleaned_data['address_control_list']
        is_enabled = address_control_list.get('is_enabled')
        address_control = address_control_list.get('address_control')
        if is_enabled:
            for address in address_control:
                mac = address.get('mac')
                ip = address.get('ip')
                # at least one, ip or mac
                if not any((mac, ip)):
                    raise forms.ValidationError('IP和MAC地址必须至少填写一个', code='ip_mac_all_empty')
        return address_control_list

    def clean_login_terminal(self):
        login_terminal = self.cleaned_data['login_terminal']
        if login_terminal.get('is_enabled'):
            if not bool(login_terminal.get('terminal_address')):
                raise forms.ValidationError('请输入终端地址')
