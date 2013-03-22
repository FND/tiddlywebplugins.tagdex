import csv

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.web.sendtiddlers import send_tiddlers
from tiddlyweb.web.util import get_route_value

from tiddlywebplugins.utils import get_store

from . import database


def get_tags(environ, start_response):
    config = environ['tiddlyweb.config']
    store = get_store(config)
    user = environ['tiddlyweb.usersign']['name'] # XXX: always present?

    start_response('200 OK', [('Content-Type', 'text/plain')])

    with database.Connection(config) as (conn, cur): # XXX: does not belong here!?
        sql = """
        SELECT DISTINCT tiddlers.bag, tags.name
        FROM tiddlers
        JOIN tiddler_tags ON tiddler_tags.tiddler_id=tiddlers.id
        JOIN tags ON tiddler_tags.tag_id=tags.id
        """
        tags_by_bag = {}
        for bag, tag in cur.execute(sql):
            tags_by_bag[bag] = tags_by_bag.get(bag) or []
            tags_by_bag[bag].append(tag)

    results = []
    for bag, tags in tags_by_bag.items():
        bag = store.get(Bag(bag))
        if not bag.policy.read or user in bag.policy.read: # XXX: duplicates existing core logic!?
            results = results + [tag for tag in tags if tag not in results] # XXX: inefficient

    return ('%s\n' % tag for tag in results) # TODO: paging


def get_tiddlers(environ, start_response):
    config = environ['tiddlyweb.config']
    store = get_store(config)
    user = environ['tiddlyweb.usersign']['name'] # XXX: always present?

    tags = get_route_value(environ, 'tags')
    tags = csv.reader([tags]).next()

    with database.Connection(config) as (conn, cur): # XXX: does not belong here!?
        sql = """
        SELECT DISTINCT bag, title FROM tiddlers
        JOIN tiddler_tags ON tiddler_tags.tiddler_id=tiddlers.id
        JOIN tags ON tiddler_tags.tag_id=tags.id
        WHERE tags.name IN (%s)
        """
        sql = sql % ', '.join('?' * len(tags))

        titles_by_bag = {}
        for bag, tag in cur.execute(sql, tags):
            titles_by_bag[bag] = titles_by_bag.get(bag) or []
            titles_by_bag[bag].append(tag)

    tiddlers = Tiddlers()
    for bag, titles in titles_by_bag.items():
        bag = store.get(Bag(bag))
        if not bag.policy.read or user in bag.policy.read: # XXX: duplicates existing core logic!?
            for title in titles:
                tiddler = Tiddler(title, bag.name)
                tiddlers.add(tiddler) # XXX: does this discard dupes?

    return send_tiddlers(environ, start_response, tiddlers)
