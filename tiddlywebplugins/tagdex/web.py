from __future__ import absolute_import, with_statement

import csv

from tiddlyweb.web.util import get_route_value

from . import database


def get_tags(environ, start_response):
    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        tags = [row[0] for row in cur.execute('SELECT name FROM tags')]
        # TODO: stream generator from the database?

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s\n' % tag for tag in tags) # TODO: paging


def get_tiddlers(environ, start_response):
    tags = get_route_value(environ, 'tags')
    tags = csv.reader([tags]).next()

    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        sql = """
        SELECT bag, title FROM tiddlers
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
        tids = cur.execute(sql, params).fetchall()
        # TODO: stream generator from the database?

    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s/%s\n' % (bag, title) for (bag, title) in tids) # TODO: paging
