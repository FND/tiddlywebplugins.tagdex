import sqlite3


DATABASE = 'tagdex.sqlite' # TODO: read from config


def init(config):
    #if 'selector' in config: # system plugin

    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        try:
            initialize_database(cur)
        except sqlite3.OperationalError: # already exists -- XXX: too magical?
            pass
        conn.commit()


def tiddler_put_hook(store, tiddler):
    #config = store.environ['tiddlyweb.config']

    with sqlite3.connect(DATABASE) as conn: # TODO: reuse connections for efficiency?
        cur = conn.cursor()

        for tag in tiddler.tags:
            # fetch or create tiddler
            tid_id = cur.execute('SELECT id FROM tiddlers WHERE title = ?',
                    (tiddler.title,))
            if not tid_id:
                tid_id = cur.execute('INSERT INTO tiddlers VALUES (?, ?, ?)',
                    (None, tiddler.title, tiddler.bag)).lastrowid

            # fetch or create tag
            tag_id = cur.execute('SELECT id FROM tags WHERE name = ?', (tag,))
            if not tag_id:
                tag_id = cur.execute('INSERT INTO tags VALUES (?, ?)',
                    (None, tag)).lastrowid

            # check or create association
            rel_id = cur.execute('SELECT * FROM tiddler_tags ' +
                    'WHERE tiddler_id = ? AND tag_id = ?', (tid_id, tag_id))
            if not rel_id:
                cur.execute('INSERT INTO tiddler_tags VALUES (?, ?)',
                    (tid_id, tag_id))

        conn.commit()


def tiddler_delete_hook(store, tiddler):
    pass # TODO


def initialize_database(cursor):
    pk = 'INTEGER PRIMARY KEY AUTOINCREMENT'
    # TODO: use `executescript`?
    cursor.execute('CREATE TABLE tags (id %s, name TEXT)' % pk)
    cursor.execute('CREATE TABLE tiddlers (id %s, title TEXT, bag TEXT)' % pk)
    cursor.execute('CREATE TABLE tiddler_tags ' +
            '(tiddler_id INTEGER, tag_id INTEGER)')
