import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tools.clean_migration_files import clean_migrations
from tools.rebuild_mysql import rebuild
from tools.clean_mongodb import clean_mongo
from tools.clean_redis import clean_redis


if __name__ == '__main__':
    clean_migrations()
    rebuild()
    clean_mongo()
    clean_redis()
