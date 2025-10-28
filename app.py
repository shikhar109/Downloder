from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "✅ YouTube Downloader Backend is Running!"

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Create a temporary directory for downloads
        temp_dir = tempfile.mkdtemp()

        # Define file path for output
        output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')

        ydl_opts = {
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True,
            'format': 'best',
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 15,
            'retries': 3,
            'extractor_retries': 3,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({'error': 'Video not found or restricted'}), 404

            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print("Error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
