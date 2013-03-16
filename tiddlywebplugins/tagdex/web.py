from __future__ import absolute_import, with_statement

from tiddlyweb.web.util import get_route_value

from . import database


def get_tags(environ, start_response):
    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        tags = [row[0] for row in cur.execute('SELECT name FROM tags')]
        # TODO: stream generator from the database?

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s\n' % tag for tag in tags) # TODO: paging


def get_tiddlers(environ, start_response):
    _filter = get_route_value(environ, 'filter')

    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        sql = """
        SELECT bag, title FROM tiddlers
        JOIN tiddler_tags ON tiddler_tags.tiddler_id=tiddlers.id
        JOIN tags ON tiddler_tags.tag_id=tags.id
        WHERE tags.name = ?
        """
        tids = cur.execute(sql, (_filter,)).fetchall()
        # TODO: stream generator from the database?

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s/%s\n' % (bag, title) for (bag, title) in tids) # TODO: paging
