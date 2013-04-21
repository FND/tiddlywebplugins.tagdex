import os
import sqlite3

from UserDict import UserDict # XXX: is this what we want?

from tiddlyweb.store import HOOKS

import tiddlywebplugins.tagdex as tagdex
import tiddlywebplugins.tagdex.hooks as hooks
import tiddlywebplugins.tagdex.database as database


def setup_module(module):
    module.CONFIG = { 'tagdex_db': 'tagdex_test.sqlite' }
    module.STORE = UserDict()
    module.STORE.environ = { 'tiddlyweb.config': CONFIG }
    module.DB = database._db_path(module.CONFIG)

    database.reset(module.CONFIG)


def test_initialization():
    assert not os.path.isfile(DB)
    tagdex.init(CONFIG)
    assert os.path.isfile(DB)

    assert hooks.tiddler_put_hook in HOOKS['tiddler']['put']
    assert hooks.tiddler_delete_hook in HOOKS['tiddler']['delete']


def test_database_reinitialization():
    assert os.path.isfile(DB)
    tagdex.init(CONFIG) # should not raise
    assert os.path.isfile(DB)


def test_indexing_on_create_and_modify():
    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = ['foo', 'bar']

    for i in xrange(2): # ensures dupes are ignored
        hooks.tiddler_put_hook(STORE, tiddler)

        tids, tags, rels = _retrieve_all()
        assert len(tids) == 1
        assert tids[0][1:] == ('HelloWorld', 'alpha')
        assert len(tags) == 2
        assert tags[0][1:] == ('foo',)
        assert tags[1][1:] == ('bar',)
        assert len(rels) == 2
        assert (tids[0][0], tags[0][0]) in rels
        assert (tids[0][0], tags[1][0]) in rels

    tiddler.tags = ['baz']
    hooks.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 1
    assert tids[0][1:] == ('HelloWorld', 'alpha')
    assert len(tags) == 1
    assert tags[0][1:] == ('baz',)
    assert len(rels) == 1
    assert (tids[0][0], tags[0][0]) in rels

    tiddler.tags = []
    hooks.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 0
    assert len(tags) == 0
    assert len(rels) == 0


def test_key_on_title_and_bag():
    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = ['foo', 'bar']
    hooks.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 1
    assert len(tags) == 2
    assert len(rels) == 2

    tiddler.bag = 'bravo'
    hooks.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 2
    assert len(tags) == 2
    assert len(rels) == 4


def test_indexing_on_delete():
    # erase previously created tiddler by blanking its tags
    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = []
    hooks.tiddler_put_hook(STORE, tiddler)

    tiddler.bag = 'bravo'
    tiddler.tags = ['aaa', 'bbb', 'ccc']
    hooks.tiddler_put_hook(STORE, tiddler)

    tiddler = UserDict()
    tiddler.title = 'LoremIpsum'
    tiddler.bag = 'bravo'
    tiddler.tags = ['...', 'bbb']
    hooks.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 2
    assert len(tags) == 4
    assert len(rels) == 5

    hooks.tiddler_delete_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 1
    assert tids[0][1] == 'HelloWorld'
    assert len(tags) == 3
    assert [tag[1] for tag in tags] == ['aaa', 'bbb', 'ccc']
    assert len(rels) == 3


def _retrieve_all():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()

        tids = database.query(cur, 'SELECT * FROM tiddlers').fetchall()
        tags = database.query(cur, 'SELECT * FROM tags').fetchall()
        rels = database.query(cur, 'SELECT * FROM tiddler_tags').fetchall()

        return tids, tags, rels
