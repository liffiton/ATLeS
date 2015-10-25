from bottle import route, static_file
from fishweb import conf


@route('/ini/<filename:path>')
def static_inis(filename):
    return static_file(filename, root=conf.INIDIR)


@route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root=conf.STATICDIR)
