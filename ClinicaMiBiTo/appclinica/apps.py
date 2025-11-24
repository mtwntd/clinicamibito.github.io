from django.apps import AppConfig

class AppclinicaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appclinica'

    def ready(self):
        import appclinica.signals