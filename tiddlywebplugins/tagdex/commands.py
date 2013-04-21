from collections import defaultdict

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.policy import PermissionsError
from tiddlyweb.web.util import check_bag_constraint
from tiddlywebplugins.utils import get_store

from . import hooks, database
from .database import query


def get_all_tags(config):
    """
    retrieve all tags
    """
    with database.Connection(config) as (conn, cur):
        for row in query(cur, 'SELECT name FROM tags'):
            yield row[0]


def get_readable_tags(environ):
    """
    retrieve tags readable by the current user
    """
    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        sql = """
        SELECT DISTINCT tiddlers.bag, tags.name
        FROM tiddlers
        JOIN tiddler_tags ON tiddler_tags.tiddler_id=tiddlers.id
        JOIN tags ON tiddler_tags.tag_id=tags.id
        """

        tags_by_bag = defaultdict(lambda: set())
        for bag, tag in query(cur, sql):
            tags_by_bag[bag].add(tag)

    results = set()
    for bag, tags in tags_by_bag.items():
        if _readable(environ, bag):
            results.update(tags)

    return results


def get_all_tagged_tiddlers(config, tags):
    """
    retrieve all tiddlers tagged with all the specified tags

    yields both a Tiddler object and the respective ID
    """
    with database.Connection(config) as (conn, cur):
        tag_ids = database.fetch_tag_ids(cur, *tags)
        tag_count = len(tags)
        if len(tag_ids) != tag_count:
            raise ValueError('tag not found') # XXX: uninformative; which one?

        sql = """
        SELECT tiddlers.id, bag, title FROM tiddlers
        LEFT JOIN tiddler_tags
        ON tiddler_tags.tiddler_id=tiddlers.id
        AND tiddler_tags.%s
        GROUP BY tiddlers.id HAVING COUNT(tiddler_tags.tag_id) = %s
        """ % ('%s', tag_count)
        if tag_count == 1:
            sql = sql % 'tag_id = ?'
            params = (tag_ids[0],)
        else:
            sql = sql % 'tag_id IN (%s)'
            sql = sql % ', '.join('?' * tag_count)
            params = tag_ids

        for _id, bag, title in query(cur, sql, params):
            yield _id, Tiddler(title, bag) # ID included for subsequent queries


def get_readable_tagged_tiddlers(environ, tags):
    """
    retrieve tiddlers tagged with all the specified tags and readable by the
    current user

    yields both a Tiddler object and the respective ID
    """
    config = environ['tiddlyweb.config']

    tids_by_bag = defaultdict(lambda: set())
    for _id, tiddler in get_all_tagged_tiddlers(config, tags):
        tids_by_bag[tiddler.bag].add((_id, tiddler.title))

    for bag, tids in tids_by_bag.items():
        if _readable(environ, bag):
            for _id, title in tids:
                yield _id, Tiddler(title, bag) # ID included for subsequent queries


def get_all_related_tags(config, tags, tiddler_ids):
    """
    retrieve all related tags for the given list of tags / tagged tiddlers
    """
    with database.Connection(config) as (conn, cur):
        sql = """
        SELECT DISTINCT name FROM tags
        JOIN tiddler_tags ON tiddler_tags.tag_id=tags.id
        JOIN tiddlers ON tiddler_tags.tiddler_id=tiddlers.id
        WHERE tiddlers.id IN (%s)
        """ % ', '.join('?' * len(tiddler_ids))

        for tag in query(cur, sql, tiddler_ids):
            tag = tag[0]
            if not tag in tags:
                yield tag


def get_readable_related_tags(environ, tags, tiddler_ids): # XXX: partially duplicates _all_ equivalent
    """
    retrieve related tags readable by the current user for the given list of
    tags / tagged tiddlers
    """
    with database.Connection(environ['tiddlyweb.config']) as (conn, cur):
        sql = """
        SELECT DISTINCT name, bag FROM tags
        JOIN tiddler_tags ON tiddler_tags.tag_id=tags.id
        JOIN tiddlers ON tiddler_tags.tiddler_id=tiddlers.id
        WHERE tiddlers.id IN (%s)
        """ % ', '.join('?' * len(tiddler_ids))

        tags_by_bag = defaultdict(lambda: set())
        for tag, bag in query(cur, sql, tiddler_ids):
            tags_by_bag[bag].add(tag)

    results = set()
    for bag, tagset in tags_by_bag.items():
        for tag in tagset:
            if not tag in tags and _readable(environ, bag):
                results.add(tag)

    return results


def reindex(config):
    """
    recreate index
    """
    database.reset(config, True)
    store = get_store(config)
    for bag in store.list_bags():
        for tiddler in store.list_bag_tiddlers(bag):
            print "processing %s/%s" % (bag.name, tiddler.title)
            hooks.tiddler_put_hook(store, tiddler)


def _readable(environ, bag_name):
    try:
        check_bag_constraint(environ, Bag(bag_name), 'read')
        return True
    except PermissionsError:
        return False
