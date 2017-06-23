import argparse
import os

import bottle
from bottle.ext import sqlite

import config
import utils
from fishweb import bottle_plugin_boxes


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--daemon', action='store_true',
                        help="run the server as a daemon (in the background)")
    parser.add_argument('--testing', action='store_true',
                        help="run the server in 'testing' mode, with debugging information, restricted to localhost, etc. -- don't do this unless you really need to")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    #host = 'localhost' if args.testing else '0.0.0.0'
    host = '0.0.0.0'

    # Create needed directories if not already there
    utils.mkdir(config.PLOTDIR)
    utils.mkdir(config.TRACKDIR)
    utils.mkdir(config.DBGFRAMEDIR)
    utils.mkdir(config.ARCHIVEDIR)

    # Setup db if not already there
    utils.init_db(config.DBFILE, config.DBSCHEMAFILE)

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, config.TEMPLATEDIR)

    app = bottle.default_app()

    # install sqlite plugin
    sqliteplugin = sqlite.Plugin(dbfile=config.DBFILE)
    app.install(sqliteplugin)

    # setup error handlers
    bottle.load("fishweb.error_handlers")

    # load modules with controllers / routes
    bottle.load("fishweb.controller_static")
    bottle.load("fishweb.controller_archive")
    bottle.load("fishweb.controller_boxes")
    bottle.load("fishweb.controller_analyze")
    bottle.load("fishweb.controller_trackview")

    if args.daemon:
        import daemon
        print("Launching server daemon in the background.")
        logfile = os.path.join(
            os.getcwd(),
            "bottle.log"
        )
        with open(logfile, 'w+') as log:
            context = daemon.DaemonContext(
                working_directory=os.getcwd(),
                stdout=log,
                stderr=log
            )
            with context:
                # add our boxes plugin
                boxes_plugin = bottle_plugin_boxes.BoxesPlugin()
                app.install(boxes_plugin)

                app.run(host=host, port=8080, server='waitress', debug=False, reloader=False)

    else:
        # add our boxes plugin
        boxes_plugin = bottle_plugin_boxes.BoxesPlugin()
        app.install(boxes_plugin)

        app.run(host=host, port=8080, server='waitress', debug=args.testing, reloader=args.testing)
