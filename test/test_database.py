import os

import tiddlywebplugins.tagdex as tagdex


def setup_module(module):
    module.CONFIG = { 'tagdex_db': 'tagdex_test.sqlite' }
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


def test_indexing():
    pass
