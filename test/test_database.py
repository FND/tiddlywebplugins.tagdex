import os

import tiddlywebplugins.tagdex as tagdex


def test_initialization():
    assert not os.path.isfile('tagdex.sqlite')
    tagdex.init(None)
    assert os.path.isfile('tagdex.sqlite')


def test_reinitialization():
    assert os.path.isfile('tagdex.sqlite')
    tagdex.init(None) # should not raise
    assert os.path.isfile('tagdex.sqlite')


def test_indexing():
    pass
