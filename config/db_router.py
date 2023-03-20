class DBRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'common':
            return 'default'
        if model._meta.app_label == 'cpexcel':
            return 'cpexceldb'
        if model._meta.app_label == 'fms':
            return 'fmsdb'
        # if model._meta.app_label == 'old_plantia':
        #     return 'plantiadb'
        if model._meta.app_label == 'plantia':
            return 'plantiav05'
        if model._meta.app_label == 'gcsystem':
            return 'GCdb'
        if model._meta.app_label == 'quality_change_management':
            return 'quality_change_management'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'common':
            return 'default'
        if model._meta.app_label == 'cpexcel':
            return 'cpexceldb'
        if model._meta.app_label == 'fms':
            return 'fmsdb'
        if model._meta.app_label == 'quality_change_management':
            return 'quality_change_management'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'common' and obj2._meta.app_label == 'fms':
            return True
        # if obj1._meta.app_label == 'old_plantia' and obj2._meta.app_label == 'fms':
        #     return True
        if obj1._meta.app_label == 'plantia' and obj2._meta.app_label == 'fms':
            return True
        if obj1._meta.app_label == 'gcsystem' and obj2._meta.app_label == 'fms':
            return True
        if obj1._meta.app_label == 'quality_change_management' and obj2._meta.app_label == 'fms':
            return True
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        if app_label == 'auth' or app_label == 'contenttypes' or app_label == 'sessions' or app_label == 'admin':
            return db == 'default'
        if app_label == 'common':
            return db == 'default'
        if app_label == 'cpexcel':
            return db == 'cpexceldb'
        if app_label == 'fms':
            return db == 'fmsdb'
        if app_label == 'quality_change_management':
            return db == 'quality_change_management'
        return None
