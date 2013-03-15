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


def _db_path(config): # XXX: partially duplicates text store's `_fixup_root` method
    path = config['tagdex_db']
    if not os.path.isabs(path):
        path = os.path.join(config.get('root_dir', ''), path)
    return path
