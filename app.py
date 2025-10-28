from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import tempfile
import os

app = Flask(__name__)
CORS(app)  # Allow Netlify frontend access

@app.route("/")
def home():
    return jsonify({"status": "✅ CutCraft Studio backend is live!"})

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "❌ No URL provided"}), 400

    url = data["url"].strip()
    temp_dir = tempfile.gettempdir()

    try:
        # Output path
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

        # yt-dlp options (no cookies, skip restricted videos)
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True,
            "geo_bypass": True,
            "ignoreerrors": True,
            "age_limit": 0,  # Skip restricted videos
            "socket_timeout": 10,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return jsonify({
                    "error": "⚠️ This video cannot be downloaded (may be age-restricted or private)."
                }), 400

            filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(filename)[0] + ".mp4"

        if not os.path.exists(file_path):
            return jsonify({"error": "❌ Download failed: File not found"}), 500

        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        return jsonify({"error": f"❌ Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
