from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import re
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "Backend online ✅"})

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get("url")

        if not url or not re.match(r'https?://', url):
            return jsonify({"error": "Invalid URL"}), 400

        temp_dir = tempfile.gettempdir()
        video_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(temp_dir, f"cutcraft_{video_id}.%(ext)s")

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "retries": 3,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(filename)[0] + ".mp4"

        if not os.path.exists(file_path):
            return jsonify({"error": "Video not found or restricted"}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )

    except Exception as e:
        error_msg = str(e)
        print("❌ Error:", error_msg)
        return jsonify({"error": f"Download failed: {error_msg}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
