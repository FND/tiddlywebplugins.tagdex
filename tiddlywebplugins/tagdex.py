import os
import sqlite3


def init(config):
    db = _db_path(config)

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        try:
            initialize_database(cur)
        except sqlite3.OperationalError: # already exists -- XXX: too magical?
            pass
        conn.commit()


def tiddler_put_hook(store, tiddler):
    db = _db_path(store.environ['tiddlyweb.config'])

    with sqlite3.connect(db) as conn: # TODO: reuse connections for efficiency?
        cur = conn.cursor()

        # fetch or create tiddler
        tid_id = _fetch_tiddler_id(tiddler, cur)
        if not tid_id:
            tid_id = cur.execute('INSERT INTO tiddlers VALUES (?, ?, ?)',
                (None, tiddler.title, tiddler.bag)).lastrowid

        # remove existing associations & orphaned tags
        tag_ids = cur.execute('SELECT tag_id FROM tiddler_tags ' +
                'WHERE tiddler_id = ?', (tid_id,)).fetchall()
        cur.execute('DELETE FROM tiddler_tags WHERE tiddler_id = ?', (tid_id,))
        for tag_id in (entry[0] for entry in tag_ids):
            _remove_orphan_tag(tag_id, cur)

        for tag in tiddler.tags:
            # fetch or create tag
            tag_id = _fetch_tag_id(tag, cur)
            if not tag_id:
                tag_id = cur.execute('INSERT INTO tags VALUES (?, ?)',
                    (None, tag)).lastrowid

            # check or create association
            rel_count = cur.execute('SELECT COUNT(*) FROM tiddler_tags ' +
                    'WHERE tiddler_id = ? AND tag_id = ?',
                    (tid_id, tag_id)).fetchone()[0]
            if not rel_count:
                cur.execute('INSERT INTO tiddler_tags VALUES (?, ?)',
                        (tid_id, tag_id))

        # remove orphaned tiddlers
        _remove_orphan_tiddler(tid_id, cur)

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


def _remove_orphan_tiddler(tid_id, cursor):
    rel_count = cursor.execute('SELECT COUNT(*) FROM tiddler_tags ' +
            'WHERE tiddler_id = ?', (tid_id,)).fetchone()[0]
    if rel_count == 0:
        cursor.execute('DELETE FROM tiddlers WHERE id = ?', (tid_id,))


def _remove_orphan_tag(tag_id, cursor):
    rel_count = cursor.execute('SELECT COUNT(*) FROM tiddler_tags ' +
            'WHERE tag_id = ?', (tag_id,)).fetchone()[0]
    if rel_count == 0:
        cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))


def _fetch_tiddler_id(tiddler, cursor):
    tid_id = (cursor.execute('SELECT id FROM tiddlers ' +
            'WHERE title = ? AND bag = ?', (tiddler.title, tiddler.bag)).
            fetchone())
    try:
        return tid_id[0]
    except TypeError:
        return False


def _fetch_tag_id(tag, cursor):
    tag_id = (cursor.execute('SELECT id FROM tags WHERE name = ?', (tag,)).
            fetchone())
    try:
        return tag_id[0]
    except TypeError:
        return False


def _db_path(config): # XXX: partially duplicates text store's `_fixup_root` method
    path = config['tagdex_db']
    if not os.path.isabs(path):
        path = os.path.join(config.get('root_dir', ''), path)
    return path
