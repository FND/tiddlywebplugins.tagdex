import sqlite3

from tiddlyweb.store import HOOKS
from tiddlyweb.manage import make_command

from . import database, hooks, commands, web


def init(config):
    HOOKS['tiddler']['put'].append(hooks.tiddler_put_hook)
    HOOKS['tiddler']['delete'].append(hooks.tiddler_delete_hook)

    with database.Connection(config, True) as (conn, cur): # TODO: emit friendly error message if configuration parameter is missing
        try:
            database.initialize(cur)
        except sqlite3.OperationalError: # already exists -- XXX: too magical?
            pass

    if 'selector' in config: # system plugin
        config['selector'].add('/tags[.{format}]', GET=web.get_tags)
        config['selector'].add('/tags/{tags:segment}[.{format}]',
                GET=web.get_tiddlers)

    @make_command() # XXX: does not belong here, but necessary for `config`!?
    def tags(args):
        """
        Display all tags or, if arguments are supplied, tagged tiddlers
        """
        if len(args) == 0:
            print '\n'.join(tag for tag in commands.get_tags(config))
        else:
            tags, tiddlers = commands.get_tiddlers(config, args)
            if len(tags):
                print '\n'.join('tag: %s' % tag for tag in tags)
            print '\n'.join('tiddler: %s/%s' % (tiddler.bag, tiddler.title)
                    for tiddler in tiddlers)
