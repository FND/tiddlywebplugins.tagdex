from __future__ import absolute_import, with_statement

from . import database


def tiddler_put_hook(store, tiddler):
    config = store.environ['tiddlyweb.config']

    with database.Connection(config, True) as (conn, cur):
        # fetch or create tiddler
        tid_id = database.fetch_tiddler_id(tiddler, cur)
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
            tag_id = database.fetch_tag_id(tag, cur)
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


def tiddler_delete_hook(store, tiddler):
    config = store.environ['tiddlyweb.config']

    with database.Connection(config, True) as (conn, cur):
        tid_id = database.fetch_tiddler_id(tiddler, cur)
        if not tid_id:
            return # XXX: should we raise an exception here? -- TODO: at least do some logging

        # remove existing associations & orphaned tiddlers and tags -- XXX: duplicates put hook logic
        tag_ids = cur.execute('SELECT tag_id FROM tiddler_tags ' +
                'WHERE tiddler_id = ?', (tid_id,)).fetchall()
        cur.execute('DELETE FROM tiddler_tags WHERE tiddler_id = ?', (tid_id,))
        cur.execute('DELETE FROM tiddlers WHERE id = ?', (tid_id,))
        for tag_id in (entry[0] for entry in tag_ids):
            _remove_orphan_tag(tag_id, cur)


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
