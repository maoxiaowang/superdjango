"""
Project settings
"""
import path
from configparser import ConfigParser

from common.log import default_logger as logger

__all__ = [
    'sys_settings'
]
parser = ConfigParser()
conf_path = os.path.join(Path(__file__).resolve().parent.parent, 'settings.ini')
# settings.ini放在项目根目录下
parser.read(conf_path)

DEFAULT_SECTION = 'DEFAULT'
ALLOW_UNDEFINED_OPTIONS = True


class BaseSection:

    def __getattr__(self, item):
        """
        通过注解类型获取配置的值
        """
        option_keys = self.__annotations__.keys()
        options = self.__annotations__
        cls_name = self.__class__.__name__
        section_name = cls_name if cls_name == DEFAULT_SECTION else cls_name.lower()
        if item not in option_keys:
            if ALLOW_UNDEFINED_OPTIONS:
                # build undefined option
                options[item] = str
            else:
                logger.warning("No option '%s' defined in section %s." % (item, section_name))
                raise AttributeError("No option '%s' defined in section %s." % (item, section_name))
        for option, a_type in options.items():
            if item == option:
                value = None
                try:
                    value = parser.get(section_name, option)
                except Exception as e:
                    logger.error("Failed to get option '%s' from section '%s'" % (option, section_name), e)
                if a_type is bool:
                    return str(value)
                if value is None:
                    return value
                return a_type.__call__(value)
        return super().__getattribute__(item)

    def __new__(cls, *args, **kwargs):
        """
        检查不支持的注解类型
        """
        super_new = super().__new__
        for attr, val in getattr(cls, '__annotations__', {}).items():
            if val not in (str, int, float, bool):
                raise AttributeError(
                    "Type %s of attribute '%s' is not supported by settings." % (val, attr)
                )
        return super_new(cls)


class DEFAULT(BaseSection):
    # add more options configured in settings.ini
    # host: str
    # debug: bool
    log_dir: str
    # session_age_seconds: int


class MySQL(BaseSection):
    host: str
    port: int
    user: str
    password: str
    name: str


class Memcached(BaseSection):
    @property
    def servers(self):
        value = self.parser.get('memcached', 'servers')
        return [item.strip() for item in value.split(',')]


class Redis(BaseSection):
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
    email_host: str
    email_port: int
    email_host_user: str
    email_host_password: str


class SystemSettings:
    DEFAULT = DEFAULT()
    mysql = MySQL()
    memcached = Memcached()
    redis = Redis()
    security = Security()
    email = Email()


sys_settings = SystemSettings()

if __name__ == "__main__":
    print(sys_settings.DEFAULT.log_dir)
