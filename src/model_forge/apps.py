from django.apps import AppConfig, apps


class ModelForgeConfig(AppConfig):
    name = 'model_forge'
    app_label = 'model_forge'

    @classmethod
    def ensure_ready(cls):
        if cls.app_label in apps.app_configs:
            return
        app_config = AppConfig.create(__package__)
        app_config.apps = apps
        app_config.label = cls.app_label
        apps.app_configs[app_config.label] = app_config
        app_config.import_models()
        apps.clear_cache()
