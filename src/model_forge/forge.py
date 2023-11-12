import inspect
import logging
from typing import Type

from django.apps import apps
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.models import Model

from model_forge.apps import ModelForgeConfig


def _registered(model: Type[Model]):
    models = {
        m.__qualname__: m
        for m in apps.get_app_config(ModelForgeConfig.app_label).get_models()
    }
    return models.get(model.__qualname__, None)


def _register_model(model: Type[Model]) -> Type[Model]:
    """ Add model to the django app registry """

    # if the model had been registered before
    if registered := _registered(model):
        return registered

    logging.debug(f'Registering model {model.__name__}')
    apps.register_model(ModelForgeConfig.app_label, model)

    return model


def _get_connection():
    db = getattr(settings, 'FAKED_MODELS_DB_ALIAS', DEFAULT_DB_ALIAS)
    return connections[db]


def _migrate(model: Type[Model]):
    """ migrate model """
    if model._meta.db_table in _get_connection().introspection.table_names():
        return

    logging.debug(f'Migrating model {model.__name__}...')

    apps.do_pending_operations(model)
    apps.clear_cache()

    connection = _get_connection()
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)


def reforge(model: Type[Model]) -> Type[Model]:
    """
    Reforge a model: This will ensure it is migrated and return it ready to use.
    """
    if not issubclass(model, Model):
        raise TypeError(f"{model} doesn't seem to be a django model.")

    ModelForgeConfig.ensure_ready()

    setattr(model, '_reforged', True)

    _migrate(model)
    return _register_model(model)


def forge(name, prefix: str = None, fields: dict = None, meta: dict = None,
          superclasses: tuple[Type[Model]] = (Model,), **kwargs) -> Type[Model]:
    """
    Create a new model class on the fly

    :param name: The new model's name.
    :param prefix: Add a custom prefix to the model's name, if not specified, and, if there's no app_label in meta,
                   use the caller's module name.
                   This ensures that there are no name conflicts models with the same name.
    :param superclasses: Tuple of superclasses to inherit from. Defaults to just the base model, unless specified.
    :param fields: Fields (and attributes) for the new model.
    :param meta: Attributes for the inner class Model.Meta.
    :param kwargs: They will be passed to ModelBase.__new__.
    :return: The newly created model class.
    """

    if not fields:
        fields = {}

    if not meta:
        meta = {}

    if prefix is None:
        call_context = inspect.stack()[1]
        call_module = inspect.getmodule(call_context[0])
        prefix = call_module.__name__.replace('.', '_').lower()

    if 'app_label' not in meta:
        name = '_'.join([prefix, name])
        meta['app_label'] = ModelForgeConfig.app_label

    known_models = {
        model.__name__.lower(): model
        for model in apps.get_app_config(ModelForgeConfig.app_label).get_models()
    }

    if name.lower() in known_models:
        return known_models[name.lower()]

    if not any(map(lambda s: issubclass(s, Model), superclasses)):
        raise TypeError('There must be at least one subclass of `django.db.models.base.ModelBase` in superclasses!')

    attrs = {
        '__module__': __package__,
        '__name__': name,
        'Meta': type('Meta', (object,), meta)
    } | fields

    model: Type[Model] = type(name, superclasses, attrs, **kwargs)  # type: ignore

    return reforge(model)
