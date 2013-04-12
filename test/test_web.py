import os
import json

import httplib2
import wsgi_intercept

from UserDict import UserDict # XXX: is this what we want?

from wsgi_intercept import httplib2_intercept
from pyquery import PyQuery as pq

from tiddlyweb.model.tiddler import tags_list_to_string
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
    _put_tiddler('1984', 'alpha', ['book', 'scifi', 'political'], 'Orwell, G.')
    _put_tiddler('Foundation', 'alpha', ['book', 'scifi'], 'Asimov, I.')


def test_tag_collection():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    tags, tiddlers = _extract_data(content)
    assert len(tiddlers) == 0
    assert len(tags) == 6
    uris = tags.values()
    tags = tags.keys()
    for tag in ['foo', 'bar', 'baz', 'book', 'scifi', 'political']:
        assert tag in tags
        assert '/tags/%s' % tag in uris
    assert not 'secret' in tags


def test_tiddler_collection():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags/foo',
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/tags/bar,foo">bar</a>' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert not 'baz' in content
    assert not 'secret' in content
    assert not 'Lipsum' in content

    response, content = http.request('http://example.org:8001/tags/bar',
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/tags/bar,foo">foo</a>' in content
    assert '<a href="/tags/bar,baz">baz</a>' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content
    assert not 'secret' in content

    response, content = http.request('http://example.org:8001/tags/foo,baz',
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert '<a href="/tags/bar,baz,foo">bar</a>' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content
    assert not 'secret' in content

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    assert not '/tags/' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content


def test_permission_handling():
    http = httplib2.Http()

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })
    tags, _ = _extract_data(content)
    assert len(tags) == 6
    assert 'foo' in tags
    assert 'bar' in tags
    assert 'baz' in tags
    assert 'book' in tags
    assert 'scifi' in tags
    assert 'political' in tags
    assert not 'secret' in tags

    # ensure a single readable tiddler suffices
    _put_tiddler('AllEyes', 'bravo', ['secret'], '...')

    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })
    lines = content.splitlines()
    tags, _ = _extract_data(content)
    assert len(tags) == 7
    assert 'secret' in tags

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'text/html' })
    assert not '/tags/' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/bravo/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content

    bag = Bag('bravo')
    bag.policy = Policy(read=['bob'])
    STORE.put(bag)

    response, content = http.request('http://example.org:8001/tags/foo,bar,baz',
            method='GET', headers={ 'Accept': 'application/json' })
    assert not '/tags/' in content
    assert '<a href="/bags/alpha/tiddlers/HelloWorld">HelloWorld</a>' in content
    assert '<a href="/bags/alpha/tiddlers/Lipsum">Lipsum</a>' in content
    assert not '/bags/bravo/tiddlers/HelloWorld' in content


def _put_tiddler(title, bag, tags, body):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)
    tags = tags_list_to_string(tags)
    rep = 'tags: %s\n\n%s' % (tags, body)

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


def _extract_data(html):
    doc = pq(html)
    tags = _get_section_links(doc, "#tags")
    tiddlers = _get_section_links(doc, "#tiddlers")
    return tags, tiddlers


def _get_section_links(doc, section_id):
    el = doc(section_id).next()
    links = {}
    while el and not el.is_("h1, h2, h3, h4, h5, h6"): # stop at next section
        link = el if el.is_("a") else el.find("a:first")
        if link:
            label = link.text().strip()
            uri = link.attr("href")
            links[label] = uri
        el = el.next()
    return links
