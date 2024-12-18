#!/usr/bin/env python3

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import brotli
import mimetypes

class BrotliHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests and serve Brotli-compressed files when available."""
        if self.path.endswith('.br'):
            # Serve the .br file with appropriate headers
            self.serve_brotli_file()
        else:
            # Check if a Brotli version of the file exists
            file_path = self.path.lstrip('/')
            brotli_file = f"{file_path}.br"
            if os.path.isfile(brotli_file):
                self.path += '.br'  # Redirect to the Brotli file
                self.serve_brotli_file()
            else:
                super().do_GET()  # Fall back to default handler

    def serve_brotli_file(self):
        """Serve a Brotli-compressed file with correct headers."""
        brotli_file_path = self.translate_path(self.path)
        if os.path.isfile(brotli_file_path):
            self.send_response(200)
            self.send_header("Content-Encoding", "br")
            content_type, _ = mimetypes.guess_type(self.path[:-3])  # Guess type without '.br'
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(os.path.getsize(brotli_file_path)))
            self.end_headers()
            with open(brotli_file_path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            self.send_error(404, "File not found")

# Set up the server
PORT = 8000
httpd = HTTPServer(('localhost', PORT), BrotliHTTPRequestHandler)
print(f"Serving on http://localhost:{PORT}")
httpd.serve_forever()
