import sys
import os

import tiddlywebplugins.tagdex as tagdex
import tiddlywebplugins.tagdex.hooks as hooks
import tiddlywebplugins.tagdex.database as database

from StringIO import StringIO # XXX: modern io.StringIO complains about non-Unicode
from UserDict import UserDict # XXX: is this what we want?

from tiddlyweb.manage import COMMANDS


def setup_module(module):
    config = { u'tagdex_db': u'tagdex_test.sqlite' }

    module.STORE = UserDict()
    module.STORE.environ = { 'tiddlyweb.config': config }

    # capture STDOUT
    module.STDOUT = getattr(sys, 'stdout')
    setattr(sys, 'stdout', StringIO())

    database.reset(config)
    tagdex.init(config)


def teardown_module(module):
    # restore STDOUT
    setattr(sys, 'stdout', module.STDOUT)


def test_tags_and_tagged():
    cmd = COMMANDS['tags']

    cmd([])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == '\n'

    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'alpha'
    tiddler.tags = ['foo', 'bar']
    hooks.tiddler_put_hook(STORE, tiddler)

    tiddler = UserDict()
    tiddler.title = 'HelloWorld'
    tiddler.bag = 'bravo'
    tiddler.tags = ['foo', 'bar']
    hooks.tiddler_put_hook(STORE, tiddler)

    tiddler = UserDict()
    tiddler.title = 'Lipsum'
    tiddler.bag = 'alpha'
    tiddler.tags = ['bar', 'baz']
    hooks.tiddler_put_hook(STORE, tiddler)

    sys.stdout.truncate(0) # reset

    cmd([])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == 'foo\nbar\nbaz\n'

    sys.stdout.truncate(0) # reset

    cmd(['foo'])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == 'tag: bar\ntiddler: alpha/HelloWorld\ntiddler: bravo/HelloWorld\n'

    sys.stdout.truncate(0) # reset

    cmd(['bar'])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == 'tag: foo\ntag: baz\ntiddler: alpha/HelloWorld\ntiddler: bravo/HelloWorld\ntiddler: alpha/Lipsum\n'

    sys.stdout.truncate(0) # reset

    cmd(['foo', 'bar'])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == 'tiddler: alpha/HelloWorld\ntiddler: bravo/HelloWorld\n'

    sys.stdout.truncate(0) # reset

    cmd(['foo', 'baz'])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == '\n'

    sys.stdout.truncate(0) # reset

    cmd(['foo', 'bar', 'baz'])
    sys.stdout.pos = 0
    stdout = sys.stdout.read()
    assert stdout == '\n'
