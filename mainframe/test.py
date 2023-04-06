def application(env, startResponse):
    startResponse('200 OK', [('Content-Type','text/html')])
    return [b"Hello, GitLand."]
