import os
import sqlite3


class Connection(object): # TODO: reuse connections for efficiency?
    """
    context manager to establish database connection, providing access to
    connection and cursor
    """

    def __init__(self, config, commit=False):
        self.config = config
        self.commit = commit

    def __enter__(self):
        db = _db_path(self.config)
        self.conn = sqlite3.connect(db)
        return self.conn, self.conn.cursor()

    def __exit__(self, *args):
        if self.commit:
            self.conn.commit()
        self.conn.close()


def fetch_tiddler_id(tiddler, cursor):
    tid_id = (cursor.execute('SELECT id FROM tiddlers ' +
            'WHERE title = ? AND bag = ?', (tiddler.title, tiddler.bag)).
            fetchone())
    try:
        return tid_id[0]
    except TypeError:
        return False


def fetch_tag_id(tag_name, cursor):
    tag_id = (cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,)).
            fetchone())
    try:
        return tag_id[0]
    except TypeError:
        return False


def initialize(cursor):
    """
    create database tables
    """
    pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'
    # TODO: use `executescript`?
    cursor.execute('CREATE TABLE tags (id %s, name TEXT)' % pk)
    cursor.execute('CREATE TABLE tiddlers (id %s, title TEXT, bag TEXT)' % pk)
    cursor.execute('CREATE TABLE tiddler_tags ' +
            '(tiddler_id INTEGER, tag_id INTEGER)')


def _db_path(config): # XXX: partially duplicates text store's `_fixup_root` method
    path = config['tagdex_db']
    if not os.path.isabs(path):
        path = os.path.join(config.get('root_dir', ''), path)
    return path
