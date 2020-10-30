import os
import sys

from redis import Redis

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.core.settings import sys_settings


def clean_redis():
    redis = Redis(
        socket_connect_timeout=2,
        host=sys_settings.redis.host,
        port=sys_settings.redis.port,
        password=sys_settings.redis.password
    )
    redis.flushall()
    print('  Redis data all flushed.')


if __name__ == '__main__':
    print('All redis data will be deleted!')
    user_input = input('Are you sure? (y/n): ')
    if user_input in ('y', 'yes'):
        clean_redis()
    else:
        print('Canceled')
