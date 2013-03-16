from __future__ import absolute_import, with_statement

from . import database


def get_tags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])

    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        tags = [row[0] for row in cur.execute('SELECT name FROM tags')]
        # TODO: stream generator from the database?

    return ('%s\n' % tag for tag in tags) # TODO: paging
