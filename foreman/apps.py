from django.apps import AppConfig
import os

class ForemanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'foreman'

    def ready(self):
        from . import africas_talking_sms
        if not os.environ.get('RUN_MAIN', None):
            africas_talking_sms.load_initial_asset_quantities()
