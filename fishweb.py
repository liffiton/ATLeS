import os
import sys

# 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
## Import gevent and monkey-patch before importing bottle.
#from gevent import monkey
#monkey.patch_all()

import bottle

import config
import utils
from fishweb import boxmanager


if __name__ == '__main__':
    daemonize = False
    testing = False
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1 == "--daemon":
            daemonize = True
        else:
            testing = True

    host = 'localhost' if testing else '0.0.0.0'

    # Create needed directories if not already there
    utils.mkdir(config.PLOTDIR)
    utils.mkdir(config.ARCHIVEDIR)

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, config.TEMPLATEDIR)

    # add our boxmanager plugin
    boxmanager = boxmanager.BoxManagerPlugin()
    bottle.install(boxmanager)

    # load modules with controllers / routes
    bottle.load("fishweb.controller_static")
    bottle.load("fishweb.controller_archive")
    bottle.load("fishweb.controller_experiments")
    bottle.load("fishweb.controller_analyze")
    bottle.load("fishweb.controller_trackview")

    if daemonize:
        import daemon
        print("Launching daemon in the background.")
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
                #bottle.run(host=host, port=8080, server='gevent', debug=False, reloader=False)
                bottle.run(host=host, port=8080, debug=False, reloader=False)

    else:
        # 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
        #bottle.run(host=host, port=8080, server='gevent', debug=testing, reloader=True)
        bottle.run(host=host, port=8080, debug=testing, reloader=True)
