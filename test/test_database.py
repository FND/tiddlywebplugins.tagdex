import os
import sqlite3

from UserDict import UserDict # XXX: is this what we want?

import tiddlywebplugins.tagdex as tagdex


def setup_module(module):
    module.CONFIG = { 'tagdex_db': 'tagdex_test.sqlite' }
    module.STORE = UserDict()
    module.STORE.environ = { 'tiddlyweb.config': CONFIG }
    # reset database
    module.DB = tagdex._db_path(module.CONFIG)
    try:
        os.remove(module.DB)
    except OSError:
        pass


def test_initialization():
    assert not os.path.isfile(DB)
    tagdex.init(CONFIG)
    assert os.path.isfile(DB)


def test_reinitialization():
    assert os.path.isfile(DB)
    tagdex.init(CONFIG) # should not raise
    assert os.path.isfile(DB)


def test_indexing_on_create_and_modify():
    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = ['foo', 'bar']

    for i in xrange(2): # ensures dupes are ignored
        tagdex.tiddler_put_hook(STORE, tiddler)

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
    tagdex.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 1
    assert tids[0][1:] == ('HelloWorld', 'alpha')
    assert len(tags) == 1
    assert tags[0][1:] == ('baz',)
    assert len(rels) == 1
    assert (tids[0][0], tags[0][0]) in rels

    tiddler.tags = []
    tagdex.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 0
    assert len(tags) == 0
    assert len(rels) == 0


def test_key_on_title_and_bag():
    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = ['foo', 'bar']
    tagdex.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 1
    assert len(tags) == 2
    assert len(rels) == 2

    tiddler.bag = 'bravo'
    tagdex.tiddler_put_hook(STORE, tiddler)

    tids, tags, rels = _retrieve_all()
    assert len(tids) == 2
    assert len(tags) == 2
    assert len(rels) == 4


def _retrieve_all():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()

        tids = cur.execute('SELECT * FROM tiddlers').fetchall()
        tags = cur.execute('SELECT * FROM tags').fetchall()
        rels = cur.execute('SELECT * FROM tiddler_tags').fetchall()

        return tids, tags, rels
