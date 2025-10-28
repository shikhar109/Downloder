from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import tempfile, os

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdir, 'video.%(ext)s'),
                'format': 'best[ext=mp4]/best'
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Find the downloaded video file
            for file in os.listdir(tmpdir):
                if file.endswith('.mp4'):
                    return send_file(os.path.join(tmpdir, file), as_attachment=True)

            return jsonify({"error": "Video not found"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "✅ CutCraft Studio Backend Running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
