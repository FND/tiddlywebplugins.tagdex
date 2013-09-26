import tiddlywebplugins.tagdex as tagdex

def test_initialization():
    config = {}
    tagdex.init(config)

    assert config['tagdex_db'] == 'tagdex.sqlite'
