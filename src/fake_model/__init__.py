import logging

from .faked import register, make

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

__all__ = ['register', 'make', 'DB_ALIAS']

DB_ALIAS = getattr(settings, 'FAKED_MODELS_DB_ALIAS', DEFAULT_DB_ALIAS)
connection = connections[DB_ALIAS]
if connection.vendor == 'sqlite':
    logging.critical('Running on sqlite with constraint checking disabled!')
    connection.disable_constraint_checking()
