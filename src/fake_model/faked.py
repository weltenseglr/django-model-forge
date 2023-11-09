import inspect
import logging
from typing import Type

from django.apps import apps
from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS
from django.db.models import Model

from fake_model.apps import FakeModelConfig


def _registered(model: Type[Model]):
    models = {
        m.__qualname__: m
        for m in apps.get_app_config(FakeModelConfig.app_label).get_models()
    }
    return models.get(model.__qualname__, None)


def _register_model(model: Type[Model]) -> Type[Model]:
    """ Add model to the django app registry """

    # if the model had been registered before
    if registered := _registered(model):
        return registered

    logging.debug(f'Registering model {model.__name__}')
    apps.register_model(FakeModelConfig.app_label, model)

    return model


def _get_connection():
    db = getattr(settings, 'FAKED_MODELS_DB_ALIAS', DEFAULT_DB_ALIAS)
    return connections[db]


def _migrate(model: Type[Model]):
    """ migrate model """
    if model._meta.db_table in _get_connection().introspection.table_names():
        return

    logging.debug(f'Migrating model {model.__name__}')

    apps.do_pending_operations(model)
    apps.clear_cache()

    connection = _get_connection()
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)


def register(model: Type[Model]) -> Type[Model]:
    if not issubclass(model, Model):
        raise TypeError(f"{model} doesn't seem to be a django model.")

    FakeModelConfig.ensure_ready()

    if not hasattr(model, '_faked_model'):
        setattr(model, '_faked_model', True)

    _migrate(model)
    return _register_model(model)


def make(name, prefix: str = None, fields: dict = None, meta: dict = None,
         superclasses: tuple[Type[Model]] = (Model,), **kwargs) -> Type[Model]:
    """
    Create a new model class on the fly

    :param name: The new model's name.
    :param prefix: Add a custom prefix to the model's name, if not specified, use the caller's module name.
                   This ensures that there are no name conflicts models with the same name but
    :param superclasses: Tuple of superclasses to inherit from. Defaults to just the base model, unless specified.
    :param fields: Fields (and attributes) for the new model.
    :param meta: Attributes for the inner class Model.Meta.
    :param kwargs: They will be passed to ModelBase.__new__.
    :return: The newly created model class.
    """
    if prefix is None:
        call_context = inspect.stack()[1]
        call_module = inspect.getmodule(call_context[0])
        prefix = call_module.__name__.replace('.', '_').lower()

    name = '_'.join([prefix, name])
    known_models = {
        model.__name__.lower(): model
        for model in apps.get_app_config(FakeModelConfig.app_label).get_models()
    }

    if name.lower() in known_models:
        return known_models[name.lower()]

    if not any(map(lambda s: issubclass(s, Model), superclasses)):
        raise TypeError('There must be at least one subclass of `django.db.models.base.ModelBase` in superclasses!')

    if not fields:
        fields = {}

    if not meta:
        meta = {}

    attrs = {
        '__module__': __package__,
        '__name__': name,
        'Meta': meta | {'app_label': FakeModelConfig.app_label}
    } | fields

    model: Type[Model] = type(name, superclasses, attrs, **kwargs)  # type: ignore

    return register(model)
