import csv

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.collections import Tiddlers
from tiddlyweb.model.policy import PermissionsError
from tiddlyweb.web.sendtiddlers import send_tiddlers
from tiddlyweb.web.util import get_route_value, check_bag_constraint

from . import database


def get_tags(environ, start_response):
    config = environ['tiddlyweb.config']
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

    results = set()
    for bag, tags in tags_by_bag.items():
        try:
            check_bag_constraint(environ, Bag(bag), 'read')
            results.update(set(tags))
        except PermissionsError:
            pass

    return ('%s\n' % tag for tag in results) # TODO: paging


def get_tiddlers(environ, start_response):
    config = environ['tiddlyweb.config']
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
        try:
            check_bag_constraint(environ, Bag(bag), 'read')
            for title in titles:
                tiddler = Tiddler(title, bag)
                tiddlers.add(tiddler) # XXX: does this discard dupes?
        except PermissionsError:
            pass

    return send_tiddlers(environ, start_response, tiddlers)
