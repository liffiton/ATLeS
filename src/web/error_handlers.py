from bottle import error, jinja2_template as template


# Provide custom, simple error responses for 400 and 500 errors,
# suitable for direct inclusion in alert models on the client.
@error(400)
@error(500)
def customerror(error):
    from bottle import DEBUG
    return template("error_simple", DEBUG=DEBUG, e=error)
