import os
import sys

# 2014-12-23: For now, not using gevent, as it appears to conflict with python-daemon
## Import gevent and monkey-patch before importing bottle.
#from gevent import monkey
#monkey.patch_all()

import bottle

from fishweb import (  # noqa -- flake8 doesn't like importing things we're not *explicitly* using
    conf,
    controller_static,
    controller_archive,
    controller_experiments,
    controller_analyze,
    controller_trackview,
    utils
)


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
    utils.mkdir(conf.PLOTDIR)
    utils.mkdir(conf.ARCHIVEDIR)

    # let bottle know where to find our templates
    bottle.TEMPLATE_PATH.insert(0, conf.TEMPLATEDIR)

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
