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

    database.reset(cfg)

    module.STORE.put(Bag('alpha'))
    module.STORE.put(Bag('bravo'))
    bag = Bag('charlie')
    bag.policy = Policy(read=['bob'])
    module.STORE.put(bag)

    _put_tiddler('HelloWorld', 'alpha', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('HelloWorld', 'bravo', ['foo', 'bar'], 'lorem ipsum')
    _put_tiddler('Lipsum', 'alpha', ['bar', 'baz'], '...')
    _put_tiddler('Confidential', 'charlie', ['private', 'secret'], '...')
    _put_tiddler('1984', 'alpha', ['book', 'scifi', 'political'], 'Orwell, G.')
    _put_tiddler('Foundation', 'alpha', ['book', 'scifi'], 'Asimov, I.')


def test_tag_collection():
    tags, tiddlers = _get_html_data('/tags')
    assert len(tiddlers) == 0
    assert len(tags) == 6
    uris = tags.keys()
    tags = tags.values()
    for tag in ['foo', 'bar', 'baz', 'book', 'scifi', 'political']:
        assert tag in tags
        assert '/tags/%s' % tag in uris
    assert not 'secret' in tags


def test_tiddler_collection(): # TODO: rename
    tags, tiddlers = _get_html_data('/tags/foo', True)
    assert len(tags) == 1
    assert ('/tags/bar,foo', 'bar') in tags
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/HelloWorld', 'HelloWorld') in tiddlers
    assert ('/bags/bravo/tiddlers/HelloWorld', 'HelloWorld') in tiddlers

    tags, tiddlers = _get_html_data('/tags/bar', True)
    assert len(tags) == 2
    assert ('/tags/bar,foo', 'foo') in tags
    assert ('/tags/bar,baz', 'baz') in tags
    assert len(tiddlers) == 3
    assert ('/bags/alpha/tiddlers/HelloWorld', 'HelloWorld') in tiddlers
    assert ('/bags/bravo/tiddlers/HelloWorld', 'HelloWorld') in tiddlers
    assert ('/bags/alpha/tiddlers/Lipsum', 'Lipsum') in tiddlers

    tags, tiddlers = _get_html_data('/tags/book', True)
    assert len(tags) == 2
    assert ('/tags/book,scifi', 'scifi') in tags
    assert ('/tags/book,political', 'political') in tags
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers
    assert ('/bags/alpha/tiddlers/Foundation', 'Foundation') in tiddlers

    tags, tiddlers = _get_html_data('/tags/scifi', True)
    assert len(tags) == 2
    assert ('/tags/book,scifi', 'book') in tags
    assert ('/tags/political,scifi', 'political') in tags
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers
    assert ('/bags/alpha/tiddlers/Foundation', 'Foundation') in tiddlers

    tags, tiddlers = _get_html_data('/tags/book,scifi', True)
    assert len(tags) == 1
    assert ('/tags/book,political,scifi', 'political') in tags
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers
    assert ('/bags/alpha/tiddlers/Foundation', 'Foundation') in tiddlers

    tags, tiddlers = _get_html_data('/tags/scifi,book', True)
    assert len(tags) == 1
    assert ('/tags/book,political,scifi', 'political') in tags
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers
    assert ('/bags/alpha/tiddlers/Foundation', 'Foundation') in tiddlers

    tags, tiddlers = _get_html_data('/tags/book,political', True)
    assert len(tags) == 1
    assert ('/tags/book,political,scifi', 'scifi') in tags
    assert len(tiddlers) == 1
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers

    tags, tiddlers = _get_html_data('/tags/book,scifi,political', True)
    assert len(tags) == 0
    assert len(tiddlers) == 1
    assert ('/bags/alpha/tiddlers/1984', '1984') in tiddlers

    tags, tiddlers = _get_html_data('/tags/foo,baz', True)
    assert len(tags) == 0
    assert len(tiddlers) == 0

    tags, tiddlers = _get_html_data('/tags/foo,bar,baz', True)
    assert len(tags) == 0
    assert len(tiddlers) == 0


def test_permission_handling():
    tags, _ = _get_html_data('/tags')
    assert len(tags) == 6
    tag_names = tags.values()
    assert 'foo' in tag_names
    assert 'bar' in tag_names
    assert 'baz' in tag_names
    assert 'book' in tag_names
    assert 'scifi' in tag_names
    assert 'political' in tag_names
    assert not 'secret' in tag_names

    tags, tiddlers = _get_html_data('/tags/secret')
    assert len(tags) == 0
    assert len(tiddlers) == 0

    tags, tiddlers = _get_html_data('/tags/private')
    assert len(tags) == 0
    assert len(tiddlers) == 0

    tags, tiddlers = _get_html_data('/tags/private,secret')
    assert len(tags) == 0
    assert len(tiddlers) == 0

    # ensure a single readable tiddler suffices for the tag to show up

    _put_tiddler('AllEyes', 'bravo', ['secret'], '...')

    tags, _ = _get_html_data('/tags')
    assert len(tags) == 7
    assert 'secret' in tags.values()

    tags, tiddlers = _get_html_data('/tags/secret', True)
    assert len(tags) == 0
    assert len(tiddlers) == 1
    assert ('/bags/bravo/tiddlers/AllEyes', 'AllEyes') in tiddlers

    tags, tiddlers = _get_html_data('/tags/private')
    assert len(tags) == 0
    assert len(tiddlers) == 0

    tags, tiddlers = _get_html_data('/tags/private,secret')
    assert len(tags) == 0
    assert len(tiddlers) == 0

    _put_tiddler('AllEyes', 'bravo', ['private', 'secret'], '...')

    tags, tiddlers = _get_html_data('/tags/secret', True)
    assert len(tags) == 1
    assert ('/tags/private,secret', 'private') in tags
    assert len(tiddlers) == 1
    assert ('/bags/bravo/tiddlers/AllEyes', 'AllEyes') in tiddlers

    tags, tiddlers = _get_html_data('/tags/private', True)
    assert len(tags) == 1
    assert ('/tags/private,secret', 'secret') in tags
    assert len(tiddlers) == 1
    assert ('/bags/bravo/tiddlers/AllEyes', 'AllEyes') in tiddlers

    tags, tiddlers = _get_html_data('/tags/private,secret', True)
    assert len(tags) == 0
    assert len(tiddlers) == 1
    assert ('/bags/bravo/tiddlers/AllEyes', 'AllEyes') in tiddlers

    tags, tiddlers = _get_html_data('/tags/foo,bar', True)
    assert len(tags) == 0
    assert len(tiddlers) == 2
    assert ('/bags/alpha/tiddlers/HelloWorld', 'HelloWorld') in tiddlers
    assert ('/bags/bravo/tiddlers/HelloWorld', 'HelloWorld') in tiddlers

    bag = Bag('bravo')
    bag.policy = Policy(read=['bob'])
    STORE.put(bag)

    tags, tiddlers = _get_html_data('/tags/foo,bar', True)
    assert len(tags) == 0
    assert len(tiddlers) == 1
    assert ('/bags/alpha/tiddlers/HelloWorld', 'HelloWorld') in tiddlers


def _put_tiddler(title, bag, tags, body):
    uri = 'http://example.org:8001/bags/%s/tiddlers/%s' % (bag, title)
    tags = tags_list_to_string(tags)
    rep = 'tags: %s\n\n%s' % (tags, body)

    http = httplib2.Http()
    response, content = http.request(uri, method='PUT',
            headers={ 'Content-Type': 'text/plain' }, body=rep)
    if not response.status == 204:
        raise RuntimeError(content)


def _get_html_data(uri, as_tuples=False):
    http = httplib2.Http()
    response, content = http.request('http://example.org:8001' + uri,
            method='GET', headers={ 'Accept': 'text/html' })
    assert response.status == 200
    assert response['content-type'] == 'text/html; charset=UTF-8'
    tags, tiddlers = _extract_data(content)
    if as_tuples:
        return tags.items(), tiddlers.items()
    else:
        return tags, tiddlers


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
    tags = _get_section_links(doc, '#tags')
    tiddlers = _get_section_links(doc, '#tiddlers')
    return tags, tiddlers


def _get_section_links(doc, section_id):
    el = doc(section_id).next()
    links = {}
    while el and not el.is_('h1, h2, h3, h4, h5, h6'): # stop at next section
        link = el if el.is_('a') else el.find('a:first')
        if link:
            label = link.text().strip()
            uri = link.attr('href')
            links[uri] = label
        el = el.next()
    return links
