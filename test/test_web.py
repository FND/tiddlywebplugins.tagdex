import os
import json

import httplib2
import wsgi_intercept

from UserDict import UserDict # XXX: is this what we want?

from wsgi_intercept import httplib2_intercept

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import Policy
from tiddlyweb.config import config
from tiddlyweb.web.serve import load_app

from tiddlywebplugins.utils import get_store

import tiddlywebplugins.tagdex as tagdex
import tiddlywebplugins.tagdex.database as database


def setup_module(module):
    cfg = _initialize_app({ 'tagdex_db': 'tagdex_test.sqlite' })
    module.STORE = get_store(cfg)

    # reset database
    db = database._db_path(cfg)
    try:
        os.remove(db)
    except OSError:
        pass

    module.STORE.put(Bag('alpha'))
    module.STORE.put(Bag('bravo'))
    bag = Bag('charlie')
    bag.policy = Policy(read=['bob'])
    module.STORE.put(bag)

    _put_tiddler('HelloWorld', 'alpha', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('HelloWorld', 'bravo', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('Lipsum', 'alpha', ['bar', 'baz'], '...')
    _put_tiddler('Confidential', 'charlie', ['secret'], '...')


def test_tag_collection():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })
    assert response.status == 200
    assert response['content-type'] == 'text/plain'
    lines = content.splitlines()
    assert len(lines) == 3
    assert 'foo' in lines
    assert 'bar' in lines
    assert 'baz' in lines


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


def test_permission_handling():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })
    lines = content.splitlines()
    assert len(lines) == 3
    assert 'foo' in lines
    assert 'bar' in lines
    assert 'baz' in lines
    assert 'secret' not in content

    # ensure a single readable tiddler suffices
    _put_tiddler('AllEyes', 'bravo', ['secret'], '...')

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })
    lines = content.splitlines()
    assert len(lines) == 4
    assert 'foo' in lines
    assert 'bar' in lines
    assert 'baz' in lines
    assert 'secret' in content

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'application/json' })
    data = json.loads(content)
    ids = ['%s/%s' % (tid['bag'], tid['title']) for tid in data]
    assert len(data) == 3
    assert 'alpha/HelloWorld' in ids
    assert 'bravo/HelloWorld' in ids
    assert 'alpha/Lipsum' in ids

    bag = Bag('bravo')
    bag.policy = Policy(read=['bob'])
    STORE.put(bag)

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'application/json' })
    data = json.loads(content)
    ids = ['%s/%s' % (tid['bag'], tid['title']) for tid in data]
    assert len(data) == 2
    assert 'alpha/HelloWorld' in ids
    assert 'bravo/HelloWorld' not in ids
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
