from __future__ import absolute_import, with_statement

import sqlite3

from tiddlyweb.store import HOOKS

from . import database, hooks


def init(config):
    HOOKS['tiddler']['put'].append(hooks.tiddler_put_hook)
    HOOKS['tiddler']['delete'].append(hooks.tiddler_delete_hook)

    with database.Connection(config, True) as (conn, cur): # TODO: emit friendly error message if configuration parameter is missing
        try:
            database.initialize(cur)
        except sqlite3.OperationalError: # already exists -- XXX: too magical?
            pass
