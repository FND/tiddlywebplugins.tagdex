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
        SELECT DISTINCT tiddlers.id, bag, title FROM tiddlers
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
        tiddlers = Tiddlers() # XXX: not required for non-web use
        tiddler_ids = []
        for tid in cur.execute(sql, params):
            tiddler = Tiddler(tid[2], tid[1])
            tiddlers.add(tiddler)
            tiddler_ids.append(tid[0])

        sql = """
        SELECT name FROM tags
        JOIN tiddler_tags ON tiddler_tags.tag_id=tags.id
        JOIN tiddlers ON tiddler_tags.tiddler_id=tiddlers.id
        WHERE tiddlers.id IN (%s)
        """
        sql = sql % ', '.join('?' * len(tiddler_ids))
        new_tags = []
        for tag in cur.execute(sql, tiddler_ids):
            tag = tag[0]
            if not (tag in tags or tag in new_tags):
                new_tags.append(tag)

    return new_tags, tiddlers
