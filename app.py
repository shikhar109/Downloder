# app.py
import os
import tempfile
import shutil
import traceback
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp
import uuid

app = Flask(__name__)
CORS(app)

# Path where cookies file will be stored if uploaded
COOKIES_FILENAME = "cookies.txt"
COOKIES_PATH = os.path.join(os.getcwd(), COOKIES_FILENAME)

# Admin key environment variable (set this in Render dashboard)
ADMIN_KEY = os.environ.get("ADMIN_KEY", None)

# sensible default user-agent list (one chosen per-download)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def has_youtube_bot_block_error(exc_text: str) -> bool:
    if not exc_text:
        return False
    lower = exc_text.lower()
    return ("sign in to confirm" in lower and "bot" in lower) or ("use --cookies" in lower) or ("cookies-from-browser" in lower)

@app.route("/")
def index():
    return jsonify({"status": "CutCraft backend running", "cookies_present": os.path.exists(COOKIES_PATH)})

@app.route("/upload_cookies", methods=["POST"])
def upload_cookies():
    """
    Upload cookies.txt via multipart/form-data with field name 'cookies'
    Must include header X-ADMIN-KEY with ADMIN_KEY value for security.
    """
    if not ADMIN_KEY:
        return jsonify({"error": "ADMIN_KEY not set on server. Set ADMIN_KEY as an environment variable."}), 500

    header_key = request.headers.get("X-ADMIN-KEY", "")
    if header_key != ADMIN_KEY:
        return jsonify({"error": "Unauthorized. Provide correct X-ADMIN-KEY header."}), 401

    if "cookies" not in request.files:
        return jsonify({"error": "No file part named 'cookies' found. Use form field 'cookies'."}), 400

    f = request.files["cookies"]
    if f.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # save file securely
    try:
        f.save(COOKIES_PATH)
        return jsonify({"status": "cookies uploaded", "path": COOKIES_PATH})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to save cookies: {str(e)}"}), 500

@app.route("/delete_cookies", methods=["POST"])
def delete_cookies():
    """
    Remove stored cookies file (protected by admin key)
    """
    header_key = request.headers.get("X-ADMIN-KEY", "")
    if header_key != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        if os.path.exists(COOKIES_PATH):
            os.remove(COOKIES_PATH)
            return jsonify({"status": "cookies deleted"})
        else:
            return jsonify({"status": "no cookies present"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def download():
    """
    Expects JSON body: {"url": "<video url>"}
    Returns file as attachment on success.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # create a unique temp dir to keep files separate
        tmpdir = tempfile.mkdtemp(prefix="cutcraft_")
        try:
            out_template = os.path.join(tmpdir, "%(title)s.%(ext)s")
            # pick a user agent
            user_agent = USER_AGENTS[0]

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": out_template,
                "noplaylist": True,
                "quiet": True,
                "nocheckcertificate": True,
                "retries": 3,
                "extractor_retries": 3,
                "socket_timeout": 20,
                "user_agent": user_agent,
                "http_headers": {
                    "User-Agent": user_agent,
                    "Referer": "https://www.youtube.com/",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            }

            # if cookies file exists on server, use it
            if os.path.exists(COOKIES_PATH):
                ydl_opts["cookiefile"] = COOKIES_PATH

            # run yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = None
                try:
                    info = ydl.extract_info(url, download=True)
                except Exception as e:
                    err_text = str(e)
                    # If yt-dlp specifically asks for cookies (YouTube bot-check), and cookies are not present -> inform client
                    if has_youtube_bot_block_error(err_text) and not os.path.exists(COOKIES_PATH):
                        # return a specific 403 telling the frontend what to do
                        return jsonify({
                            "error": "Sign in to confirm you're not a bot. Cookies required.",
                            "detail": "The video requires a logged-in session. Upload cookies.txt via /upload_cookies with your ADMIN_KEY to allow downloads."
                        }), 403
                    # If cookies exist but still failing, return the yt-dlp error for debugging
                    raise

                if not info:
                    return jsonify({"error": "Video not found or restricted"}), 404

                # get final filename
                filename = ydl.prepare_filename(info)
                # if merge_output_format added .mp4, ensure we return proper path
                if not os.path.exists(filename):
                    # try .mp4 extension
                    candidate = os.path.splitext(filename)[0] + ".mp4"
                    if os.path.exists(candidate):
                        filename = candidate

                if not os.path.exists(filename):
                    return jsonify({"error": "Download finished but file missing"}), 500

                # return file
                return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

        finally:
            # cleanup temp dir after returning file (Flask will finish streaming first).
            # remove directory children but keep attempt safe (file is already sent/sent_file uses path)
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

    except yt_dlp.utils.DownloadError as e:
        traceback.print_exc()
        txt = str(e)
        if has_youtube_bot_block_error(txt) and not os.path.exists(COOKIES_PATH):
            return jsonify({
                "error": "Sign in to confirm you're not a bot. Cookies required.",
                "detail": "Upload cookies.txt via /upload_cookies with your ADMIN_KEY."
            }), 403
        return jsonify({"error": "DownloadError: " + txt}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Download failed: " + str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
