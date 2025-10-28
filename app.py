from flask import Flask, request, send_file
import yt_dlp
import os
import tempfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend (Netlify) to call backend

@app.route('/')
def home():
    return {"message": "CutCraft API is running!"}

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')

    temp_dir = tempfile.gettempdir()

    try:
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': output_template,
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(filename)[0] + '.mp4'

        if not os.path.exists(file_path):
            return {"error": "File not found"}, 400

        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
