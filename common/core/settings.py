"""
Project settings
"""
import os
from configparser import ConfigParser
from common.utils.text import str2bool
from common.log import default_logger as logger

__all__ = [
    'conf_path',
    'sys_settings'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

parser = ConfigParser()
conf_path = os.path.join(BASE_DIR, 'settings.ini')
parser.read(conf_path)


class BaseSection:
    section = None

    def __getattr__(self, item):
        """
        通过注解类型获取配置的值
        """
        options = self.__annotations__.keys()
        if item not in options:
            logger.warning("No such options defined in section [%s]." % self.section)
            raise AttributeError("No such options defined in section [%s]." % self.section)
        for option, a_type in self.__annotations__.items():
            if item == option:
                value = None
                try:
                    value = parser.get(self.section, option)
                except Exception as e:
                    logger.warning("配置文件属性获取错误", e)
                if a_type is bool:
                    return str2bool(value)
                if value is None:
                    return value
                return a_type.__call__(value)
        return super().__getattribute__(item)

    def __new__(cls, *args, **kwargs):
        """
        检查不支持的注解类型
        """
        super_new = super().__new__
        if cls.section is None:
            raise AttributeError("The attribute 'section' requires a string value.")
        for attr, val in getattr(cls, '__annotations__', {}).items():
            if val not in (str, int, float, bool):
                raise AttributeError(
                    "Type %s of attribute '%s' is not supported by settings." % (val, attr)
                )
        return super_new(cls)


class Default(BaseSection):
    section = 'DEFAULT'
    # add more options configured in settings.ini
    host: str
    debug: bool
    log_dir: str
    session_age_seconds: int


class MySQL(BaseSection):
    section = 'mysql'
    host: str
    port: int
    user: str
    password: str
    name: str


# class MongoDB(BaseSection):
#     section = 'mongodb'
#     host: str
#     port: int


class Memcached(BaseSection):
    section = 'memcached'

    @property
    def servers(self):
        value = parser.get('memcached', 'servers')
        return [item.strip() for item in value.split(',')]


class Redis(BaseSection):
    section = 'redis'
    host: str
    port: int
    password: str
    default_db = 1

    @property
    def default_location(self):
        return ("redis://:%(password)s@%(host)s:%(port)d/%(default_db)d" %
                {'host': self.host, 'port': self.port, 'password': self.password,
                 'default_db': self.default_db}
                )


# class RabbitMQ(BaseSection):
#     section = 'rabbitmq'
#     host: str
#     port: int
#     user: str
#     password: str
#     celery_vhost: str
#
#     @property
#     def broker_url(self):
#         return ('amqp://%(user)s:%(password)s@%(host)s:%(port)d/%(vhost)s' %
#                 {'host': self.host, 'port': self.port, 'user': self.user,
#                  'password': self.password, 'vhost': self.celery_vhost}
#                 )


class Security:
    password_level = None
    password_min_length = None

    @property
    def password_validators(self):
        # min length validator
        validators = [{'NAME': 'common.core.password_validation.MinimumLengthValidator'}]
        # password policy validators
        if self.password_level == 'medium':
            validators.append({'NAME': 'common.core.password_validation.MediumLevelPasswordValidator'})
        elif self.password_level == 'high':
            validators.append({'NAME': 'common.core.password_validation.HighLevelPasswordValidator'})
        else:
            validators.append({'NAME': 'common.core.password_validation.LowLevelPasswordValidator'})
            # raise ImproperlyConfigured(
            #     'Valid choices of password level are low, medium, high.')
        return validators


class Email(BaseSection):
    section = 'email'
    email_host: str
    email_port: int
    email_host_user: str
    email_host_password: str


class SystemSettings:
    default = Default()
    mysql = MySQL()
    memcached = Memcached()
    redis = Redis()
    security = Security()
    email = Email()


sys_settings = SystemSettings()
