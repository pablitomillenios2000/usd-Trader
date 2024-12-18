from flask import Flask, send_file, abort
import os
import mimetypes

app = Flask(__name__)

@app.route('/<path:file_path>')
def serve_file(file_path):
    """
    Serve any file with the correct headers, including Brotli files.
    """
    # Resolve the absolute file path
    abs_file_path = os.path.abspath(file_path)

    # Ensure the file exists
    if not os.path.exists(abs_file_path):
        abort(404, description="File not found")

    # Guess the MIME type
    mime_type, _ = mimetypes.guess_type(abs_file_path)
    headers = {}

    # Add the Content-Encoding header for Brotli files
    if abs_file_path.endswith('.br'):
        headers['Content-Encoding'] = 'br'
        mime_type = mime_type or 'application/octet-stream'

    return send_file(abs_file_path, mimetype=mime_type, conditional=True, headers=headers)

if __name__ == "__main__":
    app.run(debug=True)
