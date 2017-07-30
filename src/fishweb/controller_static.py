from bottle import route, static_file

import config


@route('/ini/<filename:path>')
def static_inis(filename):
    return static_file(filename, root=config.INIDIR)


@route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root=config.STATICDIR)
