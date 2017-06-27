#!/usr/bin/env python3

import argparse
import os
import threading

import bottle
import bottle.ext.sqlalchemy
import sqlalchemy

import config
import utils
from fishweb import bottle_plugin_box_rpc, db_schema, track_scanner


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

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, config.TEMPLATEDIR)

    app = bottle.default_app()

    # install sqlalchemy plugin
    db_engine = sqlalchemy.create_engine('sqlite:///{}'.format(config.DBFILE))
    db_schema.create_all(db_engine)  # create db/tables if not already there
    db_plugin = bottle.ext.sqlalchemy.Plugin(
        db_engine,
        keyword='db',
        commit=True
    )
    app.install(db_plugin)

    # setup error handlers
    bottle.load("fishweb.error_handlers")

    # load modules with controllers / routes
    bottle.load("fishweb.controller_static")
    bottle.load("fishweb.controller_archive")
    bottle.load("fishweb.controller_boxes")
    bottle.load("fishweb.controller_analyze")
    bottle.load("fishweb.controller_trackview")

    # start up the track scanner
    t = threading.Thread(target=track_scanner.scan_tracks, args=[db_engine])
    t.daemon = True
    t.start()

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
                # (IIRC, this needs to be done in the daemon context,
                #  not before.)
                box_rpc_plugin = bottle_plugin_box_rpc.BoxRPCPlugin()
                app.install(box_rpc_plugin)

                app.run(host=host, port=8080, server='waitress', debug=False, reloader=False)

    else:
        # add our boxes plugin
        box_rpc_plugin = bottle_plugin_box_rpc.BoxRPCPlugin(db_engine)
        app.install(box_rpc_plugin)

        app.run(host=host, port=8080, server='waitress', debug=args.testing, reloader=args.testing)
