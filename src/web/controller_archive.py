import shutil
from bottle import post, request

import config
from common import mkdir


def _relative_move(srcroot, srcrel, destroot):
    ''' Move a file relative to a given root to a given destination.

    E.g.  relative_move('foo/', 'bar/baz', 'bob/') will move
    foo/bar/baz into bob/bar/baz, creating bob/bar if needed.
    '''
    srcfile = srcroot / srcrel
    destfile = destroot / srcrel
    mkdir(destfile.parent)  # make sure directory exists
    shutil.move(str(srcfile), str(destfile))


def _get_relpaths(basepath, trackrel):
    base_wildcard = trackrel.replace("-track.csv", "*")
    paths = basepath.glob(base_wildcard)
    for path in paths:
        yield path.relative_to(basepath)


@post('/archive/')
def post_archive():
    trackrel = request.query.trackrel
    for relpath in _get_relpaths(config.TRACKDIR, trackrel):
        _relative_move(config.TRACKDIR, relpath, config.ARCHIVEDIR)


@post('/unarchive/')
def post_unarchive():
    trackrel = request.query.trackrel
    for relpath in _get_relpaths(config.ARCHIVEDIR, trackrel):
        _relative_move(config.ARCHIVEDIR, relpath, config.TRACKDIR)
