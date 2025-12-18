#!/usr/bin/env python3
"""Google Home Web Controller - Flask Backend"""

import subprocess
import json
import re
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

DEVICE = "Familienzimmer"

def run_catt(command, *args):
    """Execute a catt command and return output."""
    cmd = ["catt", "-d", DEVICE] + [command] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1
    except Exception as e:
        return "", str(e), 1

def parse_catt_info(output):
    """Parse catt info output into a dict."""
    info = {
        "playing": False,
        "title": "",
        "artist": "",
        "album": "",
        "current_time": 0,
        "duration": 0,
        "volume": 50,
        "volume_muted": False,
        "player_state": "IDLE",
        "app": "",
        "image_url": ""
    }

    if not output:
        return info

    lines = output.strip().split('\n')
    for line in lines:
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip()

        if key == "player_state":
            info["player_state"] = value
            info["playing"] = value == "PLAYING"
        elif key == "current_time":
            try:
                info["current_time"] = float(value)
            except:
                pass
        elif key == "duration":
            try:
                info["duration"] = float(value)
            except:
                pass
        elif key == "volume_level":
            try:
                info["volume"] = int(float(value) * 100)
            except:
                pass
        elif key == "volume_muted":
            info["volume_muted"] = value == "True"
        elif key == "display_name":
            info["app"] = value

    # Parse media_metadata for title, artist, album, image
    if "media_metadata:" in output:
        try:
            # Find the media_metadata dict in output
            match = re.search(r"media_metadata:\s*(\{.*?\})\s*(?:subtitle|$)", output, re.DOTALL)
            if match:
                # This is tricky - catt outputs Python dict format, not JSON
                metadata_str = match.group(1)
                # Try to extract title, artist, album with regex
                title_match = re.search(r"'title':\s*['\"]([^'\"]+)['\"]", metadata_str)
                artist_match = re.search(r"'artist':\s*['\"]([^'\"]+)['\"]", metadata_str)
                album_match = re.search(r"'albumName':\s*['\"]([^'\"]+)['\"]", metadata_str)

                if title_match:
                    info["title"] = title_match.group(1)
                if artist_match:
                    info["artist"] = artist_match.group(1)
                if album_match:
                    info["album"] = album_match.group(1)

                # Extract first image URL
                img_match = re.search(r"'url':\s*['\"]([^'\"]+)['\"]", metadata_str)
                if img_match:
                    info["image_url"] = img_match.group(1)
        except:
            pass

    return info

@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')

@app.route('/api/info')
def get_info():
    """Get current playback info."""
    stdout, stderr, code = run_catt("info")
    if code != 0 and "Nothing is currently playing" in stderr:
        return jsonify({"playing": False, "player_state": "IDLE", "volume": 50})

    info = parse_catt_info(stdout)
    return jsonify(info)

@app.route('/api/play', methods=['POST'])
def play():
    """Resume playback."""
    stdout, stderr, code = run_catt("play")
    return jsonify({"success": code == 0, "message": stderr if code != 0 else "Playing"})

@app.route('/api/pause', methods=['POST'])
def pause():
    """Pause playback."""
    stdout, stderr, code = run_catt("pause")
    return jsonify({"success": code == 0, "message": stderr if code != 0 else "Paused"})

@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop playback."""
    stdout, stderr, code = run_catt("stop")
    return jsonify({"success": code == 0, "message": stderr if code != 0 else "Stopped"})

@app.route('/api/volume/<int:level>', methods=['POST'])
def set_volume(level):
    """Set volume (0-100)."""
    level = max(0, min(100, level))
    stdout, stderr, code = run_catt("volume", str(level))
    return jsonify({"success": code == 0, "volume": level})

@app.route('/api/volumeup', methods=['POST'])
def volume_up():
    """Increase volume by 10."""
    stdout, stderr, code = run_catt("volumeup", "10")
    return jsonify({"success": code == 0})

@app.route('/api/volumedown', methods=['POST'])
def volume_down():
    """Decrease volume by 10."""
    stdout, stderr, code = run_catt("volumedown", "10")
    return jsonify({"success": code == 0})

@app.route('/api/seek/<time>', methods=['POST'])
def seek(time):
    """Seek to position."""
    stdout, stderr, code = run_catt("seek", time)
    return jsonify({"success": code == 0})

@app.route('/api/skip', methods=['POST'])
def skip():
    """Skip current track."""
    stdout, stderr, code = run_catt("skip")
    return jsonify({"success": code == 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
