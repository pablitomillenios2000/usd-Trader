#!/usr/bin/env python3

from wsgiref.simple_server import make_server
import os

def app(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    file_path = os.path.join('.', path)
    if os.path.exists(file_path) and path.endswith('.br'):
        status = '200 OK'
        headers = [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Encoding', 'br')
        ]
        with open(file_path, 'rb') as f:
            content = f.read()
        start_response(status, headers)
        return [content]
    else:
        status = '404 Not Found'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [b'File not found']

if __name__ == '__main__':
    with make_server('', 8000, app) as httpd:
        print("Serving on port 8000...")
        httpd.serve_forever()

    print("Server stopped.")