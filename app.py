from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
import tempfile

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"message": "✅ Cut Craft Studio Backend is Running"}), 200


@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({"error": "No YouTube URL provided"}), 400

        # Create a temporary file for video download
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "video.mp4")

        # yt-dlp options
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_path,
            "quiet": True,
            "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
            "noplaylist": True,
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Send the video file for download
        return send_file(output_path, as_attachment=True, download_name="CutCraftStudio.mp4")

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up temp files
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
