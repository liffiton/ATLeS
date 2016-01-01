from bottle import error, template


# Provide custom, simple error responses for 400 and 500 errors,
# suitable for direct inclusion in alert models on the client.
@error(400)
@error(500)
def customerror(error):
    return template("error_simple", e=error)
