import os
import json

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

    store.put(Bag('alpha'))
    store.put(Bag('bravo'))

    _put_tiddler('HelloWorld', 'alpha', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('HelloWorld', 'bravo', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('Lipsum', 'alpha', ['bar', 'baz'], '...')


def test_tag_collection():
    http = httplib2.Http()
    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })

    assert response.status == 200
    assert response['content-type'] == 'text/plain'
    assert content == 'foo\nbar\nbaz\n'


def test_tiddler_collection():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags/foo',
            method='GET', headers={ 'Accept': 'text/html' })

    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert not 'Lipsum' in content

    response, content = http.request('http://example.org:8001/tags/bar',
            method='GET', headers={ 'Accept': 'text/html' })

    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content

    response, content = http.request('http://example.org:8001/tags/foo,baz',
            method='GET', headers={ 'Accept': 'text/html' })

    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'application/json' })

    assert response.status == 200
    assert response['content-type'] == 'application/json; charset=UTF-8'
    data = json.loads(content)
    ids = ['%s/%s' % (tid['bag'], tid['title']) for tid in data]
    assert len(data) == 3
    assert 'alpha/HelloWorld' in ids
    assert 'bravo/HelloWorld' in ids
    assert 'alpha/Lipsum' in ids


def _put_tiddler(title, bag, tags, body):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)
    rep = 'tags: %s\n\n%s' % (' '.join(tags), body)

    http = httplib2.Http()
    response, content = http.request(uri, method='PUT',
            headers={ 'Content-Type': 'text/plain' }, body=rep)

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
