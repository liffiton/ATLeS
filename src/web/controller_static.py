from bottle import route, static_file

import config


@route('/ini/<filename:path>')
def static_inis(filename):
    return static_file(filename, root=str(config.INIDIR))


@route('/static/<filename:path>')
def static(filename):
    return static_file(filename, root=str(config.STATICDIR))


@route('/data/<filename:path>')
def static_data(filename):
    if filename.endswith('.csv'):
        return static_file(filename, root=str(config.DATADIR), mimetype='text/plain')
    else:
        return static_file(filename, root=str(config.DATADIR))
