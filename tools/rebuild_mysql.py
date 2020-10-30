"""
Rebuild database
"""
import os
import sys

from common.core.db import MySQL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from common.core.settings import sys_settings


def rebuild():
    conn = MySQL(connect_db=False).client
    cur = None
    try:
        cur = conn.cursor()
        drop_sql = 'DROP DATABASE IF EXISTS %s' % sys_settings.mysql.name
        cur.execute(drop_sql)
    except Exception:
        pass
    if cur:
        cur.close()
    print('  MySQL database %s dropped.' % sys_settings.mysql.name)
    cur = conn.cursor()
    sql = 'CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARSET utf8 COLLATE utf8_bin' % sys_settings.mysql.name
    cur.execute(sql)
    cur.close()
    conn.close()
    print('  MySQL database %s created.' % sys_settings.mysql.name)


if __name__ == '__main__':
    print('All data will be permanently erased!')
    _y = True
    if '-y' not in sys.argv:
        user_input = input('Are you sure? (y/n): ')
        if user_input not in ('y', 'yes'):
            _y = False
    if _y:
        rebuild()
    else:
        print('Canceled')
