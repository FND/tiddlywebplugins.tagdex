import csv

from tiddlyweb.web.sendtiddlers import send_tiddlers
from tiddlyweb.web.util import get_route_value

from . import commands


def get_tags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s\n' % tag for tag in
            commands.get_tags(environ['tiddlyweb.config'])) # TODO: paging


def get_tiddlers(environ, start_response):
    tags = get_route_value(environ, 'tags')
    tags = csv.reader([tags]).next()

    tiddlers = commands.get_tiddlers(environ['tiddlyweb.config'], tags)

    return send_tiddlers(environ, start_response, tiddlers)
