def get_tags(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ["lorem ipsum"]
