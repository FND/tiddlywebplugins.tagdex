from __future__ import absolute_import, with_statement

import sqlite3

from . import database


def init(config):
    with database.Connection(config, True) as (conn, cur): # TODO: emit friendly error message if configuration parameter is missing
        try:
            database.initialize(cur)
        except sqlite3.OperationalError: # already exists -- XXX: too magical?
            pass
