from flask import Flask, send_file, abort
import os

app = Flask(__name__)

@app.route('/<path:file_path>')
def serve_brotli(file_path):
    if os.path.exists(file_path) and file_path.endswith('.br'):
        return send_file(file_path, mimetype='application/octet-stream', as_attachment=False, conditional=True, add_etags=True, headers={"Content-Encoding": "br"})
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
