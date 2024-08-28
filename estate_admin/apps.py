from django.apps import AppConfig


class EstateAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'estate_admin'

    def ready(self):
        import estate_admin.signals
