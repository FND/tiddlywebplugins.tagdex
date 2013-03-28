import csv

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.web.sendtiddlers import send_tiddlers
from tiddlyweb.web.util import get_route_value

from . import commands, database


def get_tags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ('%s\n' % tag for tag in commands.get_readable_tags(environ))


def get_tiddlers(environ, start_response):
    config = environ['tiddlyweb.config']

    tags = get_route_value(environ, 'tags')
    tags = csv.reader([tags]).next()

    tiddlers = Tiddlers()
    for tiddler in commands.get_readable_tagged_tiddlers(environ, tags):
        tiddlers.add(tiddler)

    return send_tiddlers(environ, start_response, tiddlers)
