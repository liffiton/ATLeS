import traceback

from bottle import error, jinja2_template as template


class TrackParseError(Exception):
    def __init__(self, filename, orig_exception_info):
        self.msg = "Failed to parse {}.  Please check and correct the file, deselect it, or archive it.".format(filename)
        super(TrackParseError, self).__init__(self.msg)
        self.filename = filename
        self.orig_exception_info = orig_exception_info


# Plugin to handle custom exceptions
def exception_plugin(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TrackParseError as e:
            exception = ''.join(
                traceback.format_exception(*e.orig_exception_info)
            )
            return template('error', errormsg=e.msg, exception=exception)
    return wrapper


# Provide custom, simple error responses for 400 and 500 errors,
# suitable for direct inclusion in alert models on the client.
@error(400)
@error(500)
def customerror(error):
    from bottle import DEBUG
    return template("error_simple", DEBUG=DEBUG, e=error)
