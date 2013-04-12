import csv

from StringIO import StringIO

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.web.sendtiddlers import send_tiddlers
from tiddlyweb.web.util import get_route_value

from . import commands, database


def get_tags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])

    yield '<h1 id="tags">Tags</h1>\n'
    for tag in commands.get_readable_tags(environ):
        uri = '/tags/%s' % tag # XXX: server prefix & encoding
        yield '<a href="%s">%s</a>\n' % (uri, tag)


def get_tiddlers(environ, start_response): # TODO: rename
    config = environ['tiddlyweb.config']

    tags = get_route_value(environ, 'tags')
    tags = csv.reader([tags]).next()

    start_response('200 OK', [('Content-Type', 'text/html; charset=UTF-8')])

    tiddlers = []
    tiddler_ids = []
    for _id, tiddler in commands.get_readable_tagged_tiddlers(environ, tags): # XXX: smell
        tiddlers.append(tiddler)
        tiddler_ids.append(_id)

    yield '<h2 id="tags">Related Tags</h2>\n'
    for tag in commands.get_readable_related_tags(environ, tags, tiddler_ids):
        params = sorted(tags + [tag]) # sorting ensures consistency

        csv_out = StringIO()
        writer = csv.writer(csv_out)
        writer.writerow(params)
        csv_out.seek(0)
        params = csv_out.read().rstrip()

        uri = '/tags/%s' % params # XXX: server prefix & encoding
        yield '<a href="%s">%s</a>\n' % (uri, tag)

    yield '<h2 id="tiddlers">Tiddlers</h2>\n'
    for tiddler in tiddlers:
        uri = '/bags/%s/tiddlers/%s' % (tiddler.bag, tiddler.title) # XXX: server prefix & encoding
        yield '<a href="%s">%s</a>\n' % (uri, tiddler.title)
