import glob
import shutil
from bottle import post, request
from fishweb import conf


@post('/archive/')
def post_archive():
    logname = request.query.path
    name = logname.split('/')[-1].split('-track')[0]
    assert(name != '')
    allfiles = glob.glob(conf.LOGDIR + "%s*" % name)
    for f in allfiles:
        shutil.move(f, conf.ARCHIVEDIR)


@post('/unarchive/')
def post_unarchive():
    logname = request.query.path
    name = logname.split('/')[-1].split('-track')[0]
    allfiles = glob.glob(conf.ARCHIVEDIR + "%s*" % name)
    for f in allfiles:
        shutil.move(f, conf.LOGDIR)
