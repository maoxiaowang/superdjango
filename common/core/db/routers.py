"""
Router for database
"""

DEFAULT_DB_ALIAS = 'default'
CLIENT_DB_ALIAS = 'client'

DEFAULT_DB_APPS = [
    'alarm', 'approval', 'compute'
]

CLIENT_DB_APPS = []


class DefaultDatabaseRouter:
    """
    A router to control all OpenStack database operations on models
    in the openstack application.
    """

    def db_for_read(self, model, **hints):
        if model._meta.model_name in CLIENT_DB_APPS:
            return CLIENT_DB_ALIAS
        # if model._meta.app_label in DEFAULT_DB_APPS:
        #     return DEFAULT_DB_ALIAS
        return DEFAULT_DB_ALIAS

    def db_for_write(self, model, **hints):
        if model._meta.model_name in CLIENT_DB_APPS:
            return CLIENT_DB_ALIAS
        # if model._meta.app_label in DEFAULT_DB_APPS:
        #     return DEFAULT_DB_ALIAS
        return DEFAULT_DB_ALIAS

    def allow_relation(self, obj1, obj2, **hints):
        if (obj1._state.db in [DEFAULT_DB_ALIAS] and obj2._state.db in [DEFAULT_DB_ALIAS] or
                obj1._state.db in [CLIENT_DB_ALIAS] and obj2._state.db in [CLIENT_DB_ALIAS]):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # if db == DEFAULT_DB_ALIAS:
        #     return True
        return True
