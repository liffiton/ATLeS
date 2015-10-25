import glob
import os
import shutil
from bottle import post, request
from fishweb import conf, utils


def _get_prefix(trackfile):
    trackrel = os.path.relpath(trackfile, conf.TRACKDIR)
    prefix = trackrel.split('-track')[0]
    assert(prefix != '')
    return prefix


def _relative_move(srcroot, srcrel, destroot):
    ''' Move a file relative to a given root to a given destination.

    E.g.  relative_move('foo/', 'bar/baz', 'bob/') will move
    foo/bar/baz into bob/bar/baz, creating bob/bar if needed.
    '''
    srcrelpath, srcrelfile = os.path.split(srcrel)
    destpath = os.path.join(destroot, srcrelpath)
    utils.mkdir(destpath)
    srcfile = os.path.join(srcroot, srcrel)
    shutil.move(srcfile, destpath)


@post('/archive/')
def post_archive():
    trackfile = request.query.path
    prefix = _get_prefix(trackfile)
    allfiles = glob.glob(conf.TRACKDIR + "%s[.-]*" % prefix)
    for f in allfiles:
        relpath = os.path.relpath(f, conf.TRACKDIR)
        _relative_move(conf.TRACKDIR, relpath, conf.ARCHIVEDIR)


@post('/unarchive/')
def post_unarchive():
    trackfile = request.query.path
    prefix = _get_prefix(trackfile)
    allfiles = glob.glob(conf.ARCHIVEDIR + "%s[.-]*" % prefix)
    for f in allfiles:
        relpath = os.path.relpath(f, conf.ARCHIVEDIR)
        _relative_move(conf.ARCHIVEDIR, relpath, conf.TRACKDIR)
