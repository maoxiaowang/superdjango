"""
Clean migration files, databases ..., and make migrations
"""

import os
from django.core.management.base import BaseCommand, CommandError
from tools.clean_redis import clean_redis
from tools.clean_migration_files import clean_migrations
from tools.clean_mongodb import clean_mongo
from tools.rebuild_mysql import rebuild


def migrate_and_init():
    try:
        os.system('python3 manage.py makemigrations')
        python_exec = 'python3 manage.py'
    except Exception:
        os.system('python manage.py makemigrations')
        python_exec = 'python manage.py'

    def exec_cmd(cmd):
        os.system('%s %s' % (python_exec, cmd))

    exec_cmd('migrate')
    exec_cmd('init_roles')


class Command(BaseCommand):

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Environment preparing:'))
        clean_migrations()
        rebuild()
        #clean_mongo()
        clean_redis()
        try:
            migrate_and_init()
        except Exception as e:
            self.stdout.write(self.style.ERROR(e))
