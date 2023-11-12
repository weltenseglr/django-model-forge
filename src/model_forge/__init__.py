import logging

from .forge import reforge, forge

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

__all__ = ['reforge', 'forge', 'DB_ALIAS']

DB_ALIAS = getattr(settings, 'MODEL_FORGE_DB_ALIAS', DEFAULT_DB_ALIAS)
connection = connections[DB_ALIAS]
if connection.vendor == 'sqlite':
    logging.critical('Running on sqlite with constraint checking disabled!')
    connection.disable_constraint_checking()
