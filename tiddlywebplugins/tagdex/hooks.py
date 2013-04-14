from . import database
from .database import query


def tiddler_put_hook(store, tiddler):
    config = store.environ['tiddlyweb.config']

    with database.Connection(config, True) as (conn, cur):
        # fetch or create tiddler
        tid_id = database.fetch_tiddler_id(tiddler, cur)
        if not tid_id:
            tid_id = query(cur, 'INSERT INTO tiddlers VALUES (?, ?, ?)',
                (None, tiddler.title, tiddler.bag)).lastrowid

        # remove existing associations & orphaned tags
        tag_ids = query(cur, 'SELECT tag_id FROM tiddler_tags ' +
                'WHERE tiddler_id = ?', (tid_id,)).fetchall()
        query(cur, 'DELETE FROM tiddler_tags WHERE tiddler_id = ?', (tid_id,))
        for tag_id in (entry[0] for entry in tag_ids):
            _remove_orphan_tag(tag_id, cur)

        for tag in tiddler.tags:
            # fetch or create tag
            try:
                tag_id = database.fetch_tag_ids(cur, tag)[0]
            except IndexError:
                tag_id = query(cur, 'INSERT INTO tags VALUES (?, ?)',
                    (None, tag)).lastrowid

            # check or create association
            rel_count = query(cur, 'SELECT COUNT(*) FROM tiddler_tags ' +
                    'WHERE tiddler_id = ? AND tag_id = ?',
                    (tid_id, tag_id)).fetchone()[0]
            if not rel_count:
                query(cur, 'INSERT INTO tiddler_tags VALUES (?, ?)',
                        (tid_id, tag_id))

        # remove orphaned tiddlers
        _remove_orphan_tiddler(tid_id, cur)


def tiddler_delete_hook(store, tiddler):
    config = store.environ['tiddlyweb.config']

    with database.Connection(config, True) as (conn, cur):
        tid_id = database.fetch_tiddler_id(tiddler, cur)
        if not tid_id:
            return # XXX: should we raise an exception here? -- TODO: at least do some logging

        # remove existing associations & orphaned tiddlers and tags -- XXX: duplicates put hook logic
        tag_ids = query(cur, 'SELECT tag_id FROM tiddler_tags ' +
                'WHERE tiddler_id = ?', (tid_id,)).fetchall()
        query(cur, 'DELETE FROM tiddler_tags WHERE tiddler_id = ?', (tid_id,))
        query(cur, 'DELETE FROM tiddlers WHERE id = ?', (tid_id,))
        for tag_id in (entry[0] for entry in tag_ids):
            _remove_orphan_tag(tag_id, cur)


def _remove_orphan_tiddler(tid_id, cursor):
    rel_count = query(cursor, 'SELECT COUNT(*) FROM tiddler_tags ' +
            'WHERE tiddler_id = ?', (tid_id,)).fetchone()[0]
    if rel_count == 0:
        query(cursor, 'DELETE FROM tiddlers WHERE id = ?', (tid_id,))


def _remove_orphan_tag(tag_id, cursor):
    rel_count = query(cursor, 'SELECT COUNT(*) FROM tiddler_tags ' +
            'WHERE tag_id = ?', (tag_id,)).fetchone()[0]
    if rel_count == 0:
        query(cursor, 'DELETE FROM tags WHERE id = ?', (tag_id,))
