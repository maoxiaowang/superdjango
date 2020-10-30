import os
import sys

import pymongo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
from common.core.settings import sys_settings

client = pymongo.MongoClient(
    host=sys_settings.mongodb.host,
    port=sys_settings.mongodb.port
)

DBs = [
    'logs',
]


def clean_mongo():
    for item in DBs:
        client.drop_database(item)
        print("  Mongodb database '%s' deleted." % item)


if __name__ == '__main__':
    print('All Mongodb data will be deleted!')
    user_input = input('Are you sure? (y/n): ')
    if user_input in ('y', 'yes'):
        clean_mongo()
    else:
        print('Canceled')
