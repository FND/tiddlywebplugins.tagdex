import httplib2
import wsgi_intercept

from UserDict import UserDict # XXX: is this what we want?

from wsgi_intercept import httplib2_intercept

from tiddlyweb.config import config
from tiddlyweb.web.serve import load_app

import tiddlywebplugins.tagdex as tagdex


def setup_module(module):
    module.CONFIG = { 'tagdex_db': 'tagdex_test.sqlite' }
    module.STORE = UserDict()
    module.STORE.environ = { 'tiddlyweb.config': CONFIG }
    _initialize_app(module.CONFIG)


def test_web_collection():
    http = httplib2.Http()
    response, content = http.request('http://example.org:8001/tags',
            method='GET', headers={ 'Accept': 'text/plain' })

    assert response.status == 200
    assert response['content-type'] == 'text/plain'


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
