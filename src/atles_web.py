#!/usr/bin/env python3

import argparse
import threading

import bottle
import bottle.ext.sqlalchemy
import sqlalchemy

import config
import utils
from web import bottle_plugin_box_rpc, db_schema, track_scanner


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--testing', action='store_true',
                        help="run the server in 'testing' mode, with debugging information, automatic file reload, etc. -- don't do this unless you really need to")
    parser.add_argument('--port', type=int, default=8080,
                        help="port on which to serve the web interface (default: 8080)")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    # Create needed directories if not already there
    utils.mkdir(config.PLOTDIR)
    utils.mkdir(config.TRACKDIR)
    utils.mkdir(config.DBGFRAMEDIR)
    utils.mkdir(config.ARCHIVEDIR)

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, str(config.TEMPLATEDIR))

    app = bottle.default_app()

    # install sqlalchemy plugin
    db_engine = sqlalchemy.create_engine('sqlite:///{}'.format(config.DBFILE), connect_args={'timeout': 10})
    db_schema.create_all(db_engine)  # create db/tables if not already there
    db_plugin = bottle.ext.sqlalchemy.Plugin(
        db_engine,
        keyword='db',
        commit=True
    )
    app.install(db_plugin)

    # setup error handlers
    bottle.load("web.error_handlers")

    # load modules with controllers / routes
    bottle.load("web.controller_static")
    bottle.load("web.controller_archive")
    bottle.load("web.controller_boxes")
    bottle.load("web.controller_analyze")
    bottle.load("web.controller_trackview")

    # start up the track scanner
    t = threading.Thread(target=track_scanner.scan_tracks, args=[db_engine])
    t.daemon = True
    t.start()

    # add our boxes plugin
    box_rpc_plugin = bottle_plugin_box_rpc.BoxRPCPlugin(db_engine)
    app.install(box_rpc_plugin)

    app.run(host='0.0.0.0', port=args.port, server='waitress', debug=args.testing, reloader=args.testing)
