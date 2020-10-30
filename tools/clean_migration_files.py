"""

"""
import os
import shutil
import sys

# import guardian
from django.contrib import auth
from django.conf import settings

if not settings.configured:
    settings.configure()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

MIGRATION_DIR_NAME = 'migrations'


class CleanMedia(object):
    sub_dirs = ['users', ]

    def __init__(self):
        self.media_dir = settings.MEDIA_ROOT

    def clean(self):
        for item in self.sub_dirs:
            path = os.path.join(self.media_dir, item)
            if os.path.exists(path):
                shutil.rmtree(path)
            print("  Media directory '%s' deleted." % path)


def clean_migrations():
    if os.path.exists(BASE_DIR):
        for root, dirs, files in os.walk(BASE_DIR):
            if os.path.split(root)[-1] == MIGRATION_DIR_NAME:
                for f in files:
                    if f != '__init__.py':
                        os.remove(os.path.join(root, f))
                        print('  Migration file %s removed.' % os.path.join(root, f))

    # # clean guardian
    # guardian_migrations_dir = os.path.join(os.path.dirname(guardian.__file__), MIGRATION_DIR_NAME)
    # for f in os.listdir(guardian_migrations_dir):
    #     abs_path = os.path.join(guardian_migrations_dir, f)
    #     if os.path.isfile(abs_path) and f != '__init__.py':
    #         os.remove(abs_path)
    #         print("  Migration file '%s' removed." % abs_path)

    # clean contrib apps
    auth_migrations_dir = os.path.join(os.path.dirname(auth.__file__), MIGRATION_DIR_NAME)
    for f in os.listdir(auth_migrations_dir):
        abs_path = os.path.join(auth_migrations_dir, f)
        if os.path.isfile(abs_path) and f != '__init__.py':
            os.remove(abs_path)
            print("  Migration file '%s' removed." % abs_path)

    clean_media = CleanMedia()
    clean_media.clean()


if __name__ == '__main__':
    print('Migration files will be permanently deleted! Media files will be deleted constantly!')
    _y = True
    if '-y' not in sys.argv:
        user_input = input('Are you sure? (y/n): ')
        if user_input not in ('y', 'yes'):
            _y = False
    if _y:
        clean_migrations()
    else:
        print('Canceled')
