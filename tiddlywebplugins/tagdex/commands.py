from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers

from . import database


def get_tags(config):
    with database.Connection(config) as (conn, cur):
        tags = [row[0] for row in cur.execute('SELECT name FROM tags')]
        # TODO: stream generator from the database?
    return tags


def get_tiddlers(config, tags):
    with database.Connection(config) as (conn, cur):
        sql = """
        SELECT DISTINCT bag, title FROM tiddlers
        JOIN tiddler_tags ON tiddler_tags.tiddler_id=tiddlers.id
        JOIN tags ON tiddler_tags.tag_id=tags.id
        WHERE %s
        """
        if len(tags) == 1:
            sql = sql % 'tags.name = ?'
            params = (tags[0],)
        else:
            sql = sql % 'tags.name IN (%s)'
            sql = sql % ', '.join('?' * len(tags))
            params = tags

        # TODO: stream generator from the database?
        tiddlers = Tiddlers()
        for tid in cur.execute(sql, params).fetchall():
            tiddler = Tiddler(tid[1], tid[0])
            tiddlers.add(tiddler)

    return tiddlers
