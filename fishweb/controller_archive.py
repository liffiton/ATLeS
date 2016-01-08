import glob
import os
import shutil
from bottle import post, request

import config
import utils


def _get_prefix(trackfile):
    trackrel = os.path.relpath(trackfile, config.TRACKDIR)
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
    destfile = os.path.join(destroot, srcrel)
    srcfile = os.path.join(srcroot, srcrel)
    utils.mkdir(destpath)
    shutil.move(srcfile, destfile)


@post('/archive/')
def post_archive():
    trackfile = request.query.path
    prefix = _get_prefix(trackfile)
    allfiles = glob.glob(config.TRACKDIR + "%s[.-]*" % prefix)
    for f in allfiles:
        relpath = os.path.relpath(f, config.TRACKDIR)
        _relative_move(config.TRACKDIR, relpath, config.ARCHIVEDIR)


@post('/unarchive/')
def post_unarchive():
    trackfile = request.query.path
    prefix = _get_prefix(trackfile)
    allfiles = glob.glob(config.ARCHIVEDIR + "%s[.-]*" % prefix)
    for f in allfiles:
        relpath = os.path.relpath(f, config.ARCHIVEDIR)
        _relative_move(config.ARCHIVEDIR, relpath, config.TRACKDIR)
