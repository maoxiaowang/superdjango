import copy

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from base.constants import DEFAULT_USERS, ROLE_SYS, USER_SYS, ROLE_SEC, USER_SEC, DEFAULT_ROLES, ROLE_ADT, USER_ADT
from base.management.role_perms import system, security, audit
from base.models import User, Group as Role, Permission

ECLOUD_APP_LIST = [
    'base',
    'vserver',
    'api'
]


class Command(BaseCommand):

    def handle(self, *args, **options):
        # init default users
        self.stdout.write(self.style.MIGRATE_HEADING('Initialization for role:'))
        for item in DEFAULT_USERS:
            item.update(is_active=True)
            temp_password = item.pop('password')
            user, created = User.objects.update_or_create(defaults=item, id=item['id'])
            if created:
                item['password'] = temp_password
                user.set_password(temp_password)
                user.save()
                self.stdout.write(
                    '  Creating user "%(username)s", default password is "%(password)s"... ' % item +
                    self.style.SUCCESS('OK')
                )

        # init default roles
        role_user_name_mappings = {ROLE_SYS: USER_SYS, ROLE_SEC: USER_SEC, ROLE_ADT: USER_ADT}
        for item in DEFAULT_ROLES:
            role, created = Role.objects.update_or_create(defaults=item, id=item['id'])
            if created:
                self.stdout.write(
                    '  Creating role "%(name)s"... ' % item + self.style.SUCCESS('OK')
                )

            # 将三元分别加入对应的默认角色
            username = role_user_name_mappings[role.name]
            user = User.objects.get(username=username)
            role.user_set.add(user.id)
            self.stdout.write(
                '  Assigning user %(username)s to role %(role_name)s... ' %
                {'username': user.username, 'role_name': role.name} + self.style.SUCCESS('OK')
            )

        # check temporary user admin
        temp_user = 'admin'
        temp_password = 'password'
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            if settings.DEBUG is True:
                User.objects.create_superuser(
                    temp_user, email='temp@temp.com', password=temp_password, is_active=True
                )
                self.stdout.write(
                    '  Creating temporary superuser %(username)s, default password is "%(password)s"... ' %
                    {'username': temp_user, 'password': temp_password} + self.style.SUCCESS('OK')
                )
        else:
            if settings.DEBUG is False:
                if user.is_superuser:
                    self.stdout.write(
                        "  Deleting temporary superuser %(username)s caused by DEBUG is set to True... " %
                        {'username': temp_user} + self.style.WARNING('OK')
                    )
                    user.delete(permanent=True)

        # create default roles and assign permissions to them
        initial_roles = {
            system: DEFAULT_ROLES[0],
            security: DEFAULT_ROLES[1],
            audit: DEFAULT_ROLES[2]
        }

        # 更新permission name（描述）
        perms_from_db = [
            {
                'codename': perm_obj.codename, 'name': perm_obj.name,
                'app_label': perm_obj.content_type.app_label,
                'model': perm_obj.content_type.model
            }
            for perm_obj in Permission.objects.all()
            if perm_obj.content_type.app_label in ECLOUD_APP_LIST
        ]
        changed_count = 0
        # get all model perms
        all_model_perms = list()
        for app_label in ECLOUD_APP_LIST:
            for model_name in apps.all_models[app_label]:
                # special case
                if app_label == 'auth' and model_name == 'permission':
                    model = apps.get_model('base.Permission')
                elif app_label == 'auth' and model_name == 'group':
                    model = apps.get_model('base.Group')
                else:
                    model = apps.get_model(app_label, model_name)

                # New perms
                for codename, name in model._meta.permissions:
                    if app_label in ECLOUD_APP_LIST:
                        all_model_perms.append(
                            {'app_label': app_label, 'codename': codename,
                             'model': model._meta.model_name}
                        )
                    # Old perms
                    for perm in perms_from_db:
                        # if perm['codename'] == 'list_permission':
                        #     print(perm['app_label'])

                        if all((perm['codename'] == codename, perm['app_label'] == app_label)):
                            if perm['name'] != name:
                                try:
                                    perm_obj = Permission.objects.get(
                                        codename=codename, content_type__model=model._meta.model_name,
                                        content_type__app_label=app_label)
                                except Permission.DoesNotExist:
                                    continue
                                perm_obj.name = name
                                perm_obj.save()
                                changed_count += 1
                                self.stdout.write(
                                    '  Updating permission from %(old_name)s to %(new_name)s... ' %
                                    {'old_name': perm['name'], 'new_name': name} + self.style.SUCCESS('OK')
                                )
        if changed_count:
            self.stdout.write(
                '  Permission name updated done: %d updated.' % changed_count
            )

        # 清除多余失效权限
        redundant_count = 0
        for perm in perms_from_db:
            found = False
            for mp in all_model_perms:
                if all((mp['app_label'] == perm['app_label'],
                        mp['model'] == perm['model'], mp['codename'] == perm['codename'])):
                    found = True
                    break

            if not found:
                try:
                    count, data = Permission.objects.filter(
                        codename=perm['codename'], content_type__app_label=perm['app_label'],
                        content_type__model=perm['model']).delete()
                except Exception as e:
                    raise CommandError(e)
                else:
                    redundant_count += count
                    self.stdout.write(
                        '  Cleaning redundant permission %(perm_name)s (%(model_name)s)... ' %
                        {'perm_name': '%(app_label)s.%(codename)s' % perm, 'model_name': perm['model']} +
                        self.style.SUCCESS('OK'))
        if redundant_count:
            self.stdout.write(
                '  Redundant permission cleaned done: %d cleaned.' % redundant_count
            )

        # 初始化角色
        for role_model, role_info in initial_roles.items():
            # 角色标准权限，base/management/perms/下定义
            role_name = role_info['name']
            role = Role.objects.get(name=role_name)
            standard_role_perms = role_model.perms

            standard_role_perms_list = list()
            app_label_list = list()
            for app_label, codenames in standard_role_perms.items():
                if app_label in app_label_list:
                    raise CommandError('Duplicated app label %s. Please check %s.py to fix this issue.' %
                                       (app_label, role_model.__name__))
                app_label_list.append(app_label)
                codename_list = list()
                for codename in codenames:
                    if codename in codename_list:
                        # duplicated code name
                        raise CommandError('Duplicated code name %s.%s. Please check %s.py to fix this issue.' %
                                           (app_label, codename, role_model.__name__))
                    codename_list.append(codename)
                    standard_role_perms_list.append('%s.%s' % (app_label, codename))

            # 角色现有权限
            current_role_perms = ['%s.%s' % (item.content_type.app_label, item.codename) for
                                  item in role.permissions.all()]

            # 清理不存在（残留）的角色权限
            cleaned_count = 0
            for item in current_role_perms:
                if item not in standard_role_perms_list:
                    a, c = item.split('.')
                    perms = Permission.objects.filter(codename=c, content_type__app_label=a)
                    if perms.exists():
                        p = perms.first()
                        self.stdout.write(
                            self.style.MIGRATE_LABEL(
                                '  Found invalid role (%s) permission \'%s.%s\', trying to clean it...' %
                                (role_name, p.content_type.app_label, p.codename)))

                        role.permissions.remove(p.id)
                        cleaned_count += 1
            if cleaned_count:
                self.stdout.write(
                    self.style.SUCCESS(('  Invalid role permissions cleaned done: %d cleaned.' % cleaned_count)))

            # 重新获取角色权限
            all_role_perms = ['%s.%s' % (item.content_type.app_label, item.codename) for
                              item in role.permissions.all()]

            if len(all_role_perms) < len(standard_role_perms_list):
                missing_perms = [item for item in standard_role_perms_list if item not in all_role_perms]
                self.stdout.write(
                    self.style.MIGRATE_LABEL(
                        '  Found %d missing role permissions: \n    ' % len(missing_perms)
                    ) + '- ' + '\n    - '.join(missing_perms)

                )

                abnormal_count = 0
                for ap in missing_perms:
                    app_label, codename = ap.split('.')
                    try:
                        perm = Permission.objects.get(codename=codename, content_type__app_label=app_label)
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING('  Missing role permission fix interrupted: %d fixed.' % abnormal_count)
                        )
                        raise CommandError(
                            'Permission %s is an invalid permission. '
                            'Please check %s.py to fix this. '
                            'Or try to execute migrate commands first to initialize permissions.'
                            % (ap, role_model.__name__)
                        )
                    else:
                        role.permissions.add(perm)
                        self.stdout.write(
                            '  Assigning permission %(perm_name)s to role %(role_name)s... ' %
                            {'perm_name': ap, 'role_name': role_name} + self.style.SUCCESS('OK'))
                        abnormal_count += 1
                self.stdout.write(
                    '  Missing role permission fix done: %d fixed.' % abnormal_count
                )
            elif len(all_role_perms) > len(standard_role_perms_list):
                redundant_perms = [item for item in standard_role_perms_list if item not in all_role_perms]
                self.stdout.write(
                    self.style.MIGRATE_LABEL(
                        '  Found %d redundant role permissions: \n    ' % len(redundant_perms)
                    ) + '- ' + '\n    - '.join(redundant_perms)
                )
                redundant_count = 0
                for rp in redundant_perms:
                    app_label, codename = rp.split('.')
                    try:
                        deleted_count, _ = Permission.objects.filter(
                            codename=codename, content_type__app_label=app_label
                        ).delete()
                    except Exception:
                        self.stdout.write(
                            self.style.WARNING(
                                '  Redundant role permission fix interrupted: %d fixed.' % redundant_count
                            )
                        )
                        raise CommandError(
                            'Permission %s is an invalid permission. '
                            'Please check %s.py to fix this.'
                            % (rp, role_model.__name__)
                        )
                    else:
                        redundant_count += deleted_count
                        self.stdout.write(
                            'Deleting redundant permission %(perm_name)s from role %(role_name)s... ' %
                            {'perm_name': rp, 'role_name': role_name} + self.style.SUCCESS('OK')
                        )
                self.stdout.write(
                    '  Redundant role permission fix done: %d fixed.' % redundant_count
                )

        # 清理失效的ContentTypes
        content_types = ContentType.objects.all()
        invalid_cts = list()
        for ct in content_types:
            if ct.model not in apps.all_models[ct.app_label]:
                invalid_cts.append('%s.%s' % (ct.app_label, ct.model))
        if invalid_cts:
            # self.stdout.write(
            #     self.style.WARNING(
            #         '  Found %d invalid content types.' % len(invalid_cts))
            # )
            self.stdout.write(
                self.style.MIGRATE_LABEL('  Found %d invalid content types: \n    ' % len(invalid_cts))
                + '- ' + '\n    - '.join(invalid_cts)
            )
            invalid_ct_count = 0
            for ct in invalid_cts:
                app_label, model = ct.split('.')
                ContentType.objects.get(app_label=app_label, model=model).delete()
                self.stdout.write(
                    '  Deleting invalid content type "%(content_type)s"... ' % {'content_type': ct} +
                    self.style.SUCCESS('OK')
                )
                invalid_ct_count += 1
            self.stdout.write(
                '  Invalid content type cleaned done: %d cleaned' % invalid_ct_count
            )
        self.stdout.write(self.style.SUCCESS('  Role initialization done.'))
