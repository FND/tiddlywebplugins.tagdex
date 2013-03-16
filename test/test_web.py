import os

import httplib2
import wsgi_intercept

from UserDict import UserDict # XXX: is this what we want?

from wsgi_intercept import httplib2_intercept

from tiddlyweb.model.bag import Bag
from tiddlyweb.config import config
from tiddlyweb.web.serve import load_app

from tiddlywebplugins.utils import get_store

import tiddlywebplugins.tagdex as tagdex
import tiddlywebplugins.tagdex.database as database


def setup_module(module):
    cfg = _initialize_app({ 'tagdex_db': 'tagdex_test.sqlite' })
    store = get_store(cfg)

    # reset database
    db = database._db_path(cfg)
    try:
        os.remove(db)
    except OSError:
        pass

    bag = Bag('alpha')
    store.put(bag)

    _put_tiddler('HelloWorld', bag.name, """
tags: foo bar

lorem ipsum
dolor sit amet
    """.strip())
    _put_tiddler('Lipsum', bag.name, """
tags: bar baz

...
    """.strip())


def test_web_collection():
    http = httplib2.Http()
    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })

    assert response.status == 200
    assert response['content-type'] == 'text/plain'
    assert content == 'foo\nbar\nbaz\n'


def _put_tiddler(title, bag, body):
    http = httplib2.Http()
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)
    response, content = http.request(uri, method='PUT',
            headers={ 'Content-Type': 'text/plain' }, body=body)

    if not response.status == 204:
        raise RuntimeError(content)


def _initialize_app(cfg):
    config.update(cfg) # XXX: side-effecty
    config['server_host'] = {
        'scheme': 'http',
        'host': 'example.org',
        'port': '8001',
    }
    config['system_plugins'].append('tiddlywebplugins.tagdex')

    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('example.org', 8001, lambda: load_app())

    return config
