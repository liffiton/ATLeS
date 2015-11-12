import argparse
import os

# 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
## Import gevent and monkey-patch before importing bottle.
#from gevent import monkey
#monkey.patch_all()

import bottle

import config
import utils
from fishweb import boxmanager


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--daemon', action='store_true',
                        help="run the server as a daemon (in the background)")
    parser.add_argument('-l', '--local', action='store_true',
                        help="run experiments on this (local) machine only -- good for a standalone installation on a single machine")
    parser.add_argument('--testing', action='store_true',
                        help="run the server in 'testing' mode, with debugging information, restricted to localhost, etc. -- don't do this unless you really need to")

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()

    host = 'localhost' if args.testing else '0.0.0.0'

    # Create needed directories if not already there
    utils.mkdir(config.PLOTDIR)
    utils.mkdir(config.TRACKDIR)
    utils.mkdir(config.DBGFRAMEDIR)
    utils.mkdir(config.ARCHIVEDIR)

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, config.TEMPLATEDIR)

    app = bottle.default_app()

    # set app config
    app.config['fishweb.local'] = args.local

    # load modules with controllers / routes
    bottle.load("fishweb.controller_static")
    bottle.load("fishweb.controller_archive")
    bottle.load("fishweb.controller_experiments")
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
                # 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
                #app.run(host=host, port=8080, server='gevent', debug=False, reloader=False)
                # add our boxmanager plugin if not running locally
                # must be done after forking
                if not args.local:
                    boxmanager = boxmanager.BoxManagerPlugin()
                    app.install(boxmanager)

                app.run(host=host, port=8080, debug=False, reloader=False)

    else:
        # add our boxmanager plugin if not running locally
        if not args.local:
            boxmanager = boxmanager.BoxManagerPlugin()
            app.install(boxmanager)

        # 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
        #app.run(host=host, port=8080, server='gevent', debug=args.testing, reloader=True)
        app.run(host=host, port=8080, debug=args.testing, reloader=True)
