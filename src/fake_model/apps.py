from django.apps import AppConfig, apps


class FakeModelConfig(AppConfig):
    name = 'fake_model'
    app_label = 'faked'

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
