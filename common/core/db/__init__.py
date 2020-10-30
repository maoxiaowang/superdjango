import os
from configparser import ConfigParser

import pymongo
import pymysql
import psycopg2
from common.log import default_logger as logger
from common.core.settings import sys_settings


__all__ = [
    'MongoDB',
    'MySQL',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

conf_path = os.path.join(BASE_DIR, 'settings.ini')
parser = ConfigParser()
parser.read(conf_path)


class MySQL:

    def __init__(self, host=None, port=None, user=None, password=None, db=None, connect_db=True, **kwargs):
        self.db = db or parser.get('mysql', 'name') if connect_db else None
        self.connect_db = connect_db
        self.host = host or parser.get('mysql', 'host')
        self.port = port or parser.getint('mysql', 'port')
        self.user = user or parser.get('mysql', 'user')
        self.password = password or parser.get('mysql', 'password')

    @property
    def client(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            db=self.db,
            cursorclass=pymysql.cursors.DictCursor
        )


class PostGreSQL:

    def __init__(self, host=None, port=None, user=None, password=None, database=None, **kwargs):
        self.database = database or parser.get('postgresql', 'database')
        self.host = host or parser.get('postgresql', 'host')
        self.port = port or parser.getint('postgresql', 'port')
        self.user = user or parser.get('postgresql', 'user')
        self.password = password or parser.get('postgresql', 'password')

    @property
    def client(self):
        return psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )
    
    
class PostGreSQLHistory:

    def __init__(self, host=None, port=None, user=None, password=None, database=None, **kwargs):
        self.database = database or parser.get('postgresqlhistory', 'database')
        self.host = host or parser.get('postgresqlhistory', 'host')
        self.port = port or parser.getint('postgresqlhistory', 'port')
        self.user = user or parser.get('postgresqlhistory', 'user')
        self.password = password or parser.get('postgresqlhistory', 'password')

    @property
    def client(self):
        return psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
        )


# conn = psycopg2.connect(database="vserver_engine_history", user="vserver_engine_history",
#                         password="OMbUYE7OPtNF8Pd4JY111j", host="10.10.3.38",
#                         port="5432")

class MongoDB:
    """
    Add more staticmethod
    """

    def __init__(self, host=None, port=None, username=None, password=None,
                 tz_aware=True, connect=None, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.tz_aware = tz_aware
        self.connect = connect
        self.kwargs = kwargs

    @property
    def client(self):
        return pymongo.MongoClient(
            self.host or sys_settings.mongodb.host,
            self.port or sys_settings.mongodb.port,
            username=self.username,
            password=self.password,
            tz_aware=self.tz_aware,
            connect=self.connect,
            **self.kwargs
        )

    def db(self, db):
        return self.client[db]

    def col(self, db, col):
        return self.client[db][col]

    def col_opt_log(self):
        return self.col('logs', 'operations')


if __name__ == '__main__':
    # test mongodb
    try:
        print('Connecting MongoDB server %s...' % sys_settings.mongodb.host)
        mongo_info = pymongo.MongoClient(
            sys_settings.mongodb.host,
            sys_settings.mongodb.port,
            tz_aware=True
        )['admin']['system.version'].find_one({})
        version = 'Mongodb version: %s'
        print(version % mongo_info['version'] if mongo_info else version % 'Unknown')
    except Exception as e:
        print(str(e))
        logger.error('Testing Mongodb error: %s' % str(e))
        raise
