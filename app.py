#!/usr/bin/env python3
"""Google Home Web Controller - Flask Backend"""

import subprocess
import json
import re
import time
import os
import tempfile
import asyncio
import uuid
import requests
import shutil
from flask import Flask, render_template, jsonify, request, send_from_directory
from groq import Groq
import edge_tts

app = Flask(__name__)

DEVICE = "Familienzimmer"

# Groq API for LLM (set via environment variable)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# SHODH Cloudflare Memory API (set via environment variable)
SHODH_URL = os.environ.get("SHODH_CLOUDFLARE_URL", "")
SHODH_API_KEY = os.environ.get("SHODH_CLOUDFLARE_API_KEY", "")

# In-memory conversation history (last 5 exchanges)
conversation_history = []
MAX_HISTORY = 5

# Edge TTS Voice (German)
TTS_VOICE = "de-CH-LeniNeural"  # Swiss German female voice

# Audio files directory for casting
AUDIO_DIR = "/tmp/ghome_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Local server IP (for casting URLs) - Pi-Hole server
LOCAL_IP = "10.0.1.56"
LOCAL_PORT = 5000

# Radio stations - name: stream URL
RADIO_STATIONS = {
    "SRF 1": "https://stream.srg-ssr.ch/m/drs1/mp3_128",
    "SRF 2 Kultur": "https://stream.srg-ssr.ch/m/drs2/mp3_128",
    "SRF 3": "https://stream.srg-ssr.ch/m/drs3/mp3_128",
    "SRF 4 News": "https://stream.srg-ssr.ch/m/drs4news/mp3_128",
    "Radio Swiss Jazz": "https://stream.srg-ssr.ch/m/rsj/mp3_128",
    "Radio Swiss Classic": "https://stream.srg-ssr.ch/m/rsc_de/mp3_128",
    "Radio Swiss Pop": "https://stream.srg-ssr.ch/m/rsp/mp3_128",
    "FM4": "https://orf-live.ors-shoutcast.at/fm4-q2a",
    "Ö1": "https://orf-live.ors-shoutcast.at/oe1-q2a",
    "Ö3": "https://orf-live.ors-shoutcast.at/oe3-q2a",
    "Bayern 3": "https://dispatcher.rndfnk.com/br/br3/live/mp3/mid",
    "WDR 2": "https://wdr-wdr2-rheinland.icecastssl.wdr.de/wdr/wdr2/rheinland/mp3/128/stream.mp3",
    "NDR 2": "https://icecast.ndr.de/ndr/ndr2/niedersachsen/mp3/128/stream.mp3",
    "1LIVE": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3",
    "Klassik Radio": "https://stream.klassikradio.de/live/mp3-192/stream.klassikradio.de/",
    "Lounge FM": "http://stream.lounge.fm/loungefm-mp3-320",
}

# YouTube favorites - name: URL
YOUTUBE_FAVORITES = {
    "Hillsong Worship 2h": "https://www.youtube.com/watch?v=ruI3dhJQamM",
    "Worship Songs 2h": "https://www.youtube.com/watch?v=wUm_WP6TH3o",
    "Hillsong Best 2024": "https://www.youtube.com/watch?v=_1HGZ_9aRhI",
    "Smooth Jazz": "https://www.youtube.com/watch?v=U3n31M81RpE",
    "Jazz Fusion 70s-80s": "https://www.youtube.com/watch?v=DMI2Xh6tIIQ",
    "Rare Jazz Fusion": "https://www.youtube.com/watch?v=Qw7vOfDLBiQ",
    "Indie Jazz Funk": "https://www.youtube.com/watch?v=DxVce5xunE4",
}

# Track current playing source
current_source = {"type": None, "name": None}

def run_catt(command, *args, background=False):
    """Execute a catt command and return output."""
    cmd = ["catt", "-d", DEVICE] + [command] + list(args)
    try:
        if background:
            import os
            full_cmd = f"nohup {' '.join(cmd)} > /dev/null 2>&1 &"
            os.system(full_cmd)
            time.sleep(2)
            return "", "", 0
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

    if "media_metadata:" in output:
        try:
            match = re.search(r"media_metadata:\s*(\{.*?\})\s*(?:subtitle|$)", output, re.DOTALL)
            if match:
                metadata_str = match.group(1)
                title_match = re.search(r"'title':\s*['\"]([^'\"]+)['\"]", metadata_str)
                artist_match = re.search(r"'artist':\s*['\"]([^'\"]+)['\"]", metadata_str)
                album_match = re.search(r"'albumName':\s*['\"]([^'\"]+)['\"]", metadata_str)

                if title_match:
                    info["title"] = title_match.group(1)
                if artist_match:
                    info["artist"] = artist_match.group(1)
                if album_match:
                    info["album"] = album_match.group(1)

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

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files for casting."""
    return send_from_directory(AUDIO_DIR, filename)

@app.route('/api/info')
def get_info():
    """Get current playback info."""
    global current_source
    stdout, stderr, code = run_catt("info")
    if code != 0 and "Nothing is currently playing" in stderr:
        current_source = {"type": None, "name": None}
        return jsonify({"playing": False, "player_state": "IDLE", "volume": 50})

    info = parse_catt_info(stdout)

    if current_source["type"] == "radio" and current_source["name"]:
        if not info["title"] or "mp3" in info["title"].lower() or "stream" in info["title"].lower():
            info["title"] = current_source["name"]
            info["artist"] = "Radio"
            info["album"] = ""
            info["app"] = "Radio"

    info["source_type"] = current_source["type"]
    info["source_name"] = current_source["name"]

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
    global current_source
    stdout, stderr, code = run_catt("stop")
    current_source = {"type": None, "name": None}
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

@app.route('/api/radio/stations')
def get_stations():
    """Get list of available radio stations."""
    return jsonify({"stations": list(RADIO_STATIONS.keys())})

@app.route('/api/radio/play/<station>', methods=['POST'])
def play_radio(station):
    """Play a radio station."""
    global current_source
    if station not in RADIO_STATIONS:
        return jsonify({"success": False, "message": "Station not found"}), 404

    run_catt("stop")
    time.sleep(1)

    url = RADIO_STATIONS[station]
    stdout, stderr, code = run_catt("cast", url)

    if code == 0:
        current_source = {"type": "radio", "name": station}

    return jsonify({"success": code == 0, "station": station, "message": stderr if code != 0 else f"Playing {station}"})

@app.route('/api/youtube/list')
def get_youtube():
    """Get list of YouTube favorites."""
    return jsonify({"videos": list(YOUTUBE_FAVORITES.keys())})

@app.route('/api/youtube/play/<path:name>', methods=['POST'])
def play_youtube(name):
    """Play a YouTube favorite."""
    global current_source

    if name not in YOUTUBE_FAVORITES:
        return jsonify({"success": False, "message": f"Video '{name}' not found"}), 404

    run_catt("stop")
    time.sleep(1)

    url = YOUTUBE_FAVORITES[name]
    stdout, stderr, code = run_catt("cast", url)

    if code == 0:
        current_source = {"type": "youtube", "name": name}

    return jsonify({"success": code == 0, "name": name, "message": stderr if code != 0 else f"Playing {name}"})

# ==================== SHODH Memory Functions ====================

def shodh_recall(query, limit=3):
    """Search for relevant memories using semantic search."""
    if not SHODH_API_KEY:
        return []
    try:
        response = requests.post(
            f"{SHODH_URL}/api/recall",
            headers={
                "Authorization": f"Bearer {SHODH_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"query": query, "limit": limit},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("memories", [])
    except Exception as e:
        print(f"SHODH recall error: {e}")
    return []

def shodh_remember(content, memory_type="Conversation", tags=None):
    """Store a new memory in SHODH."""
    if not SHODH_API_KEY:
        return None
    try:
        payload = {
            "content": content,
            "type": memory_type,
            "source_type": "ai_generated"
        }
        if tags:
            payload["tags"] = tags

        response = requests.post(
            f"{SHODH_URL}/api/remember",
            headers={
                "Authorization": f"Bearer {SHODH_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"SHODH remember error: {e}")
    return None

def shodh_context(context, max_results=3, auto_ingest=True):
    """Surface relevant memories based on context."""
    if not SHODH_API_KEY:
        return {"surfaced_memories": [], "count": 0}
    try:
        response = requests.post(
            f"{SHODH_URL}/api/context",
            headers={
                "Authorization": f"Bearer {SHODH_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "context": context,
                "max_results": max_results,
                "auto_ingest": auto_ingest
            },
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"SHODH context error: {e}")
    return {"surfaced_memories": [], "count": 0}

def format_memories_for_context(memories, max_chars=500):
    """Format memories for inclusion in LLM context."""
    if not memories:
        return ""

    context_parts = []
    total_chars = 0

    for mem in memories:
        content = mem.get("content", "")
        # Truncate if needed
        if total_chars + len(content) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 50:
                content = content[:remaining] + "..."
            else:
                break
        context_parts.append(f"- {content}")
        total_chars += len(content)

    if context_parts:
        return "Relevante Erinnerungen:\n" + "\n".join(context_parts)
    return ""

# ==================== Voice Assistant (Groq + Edge TTS) ====================

def get_groq_response(text, use_memory=True):
    """Get response from Groq LLM with optional memory context."""
    global conversation_history

    if not groq_client:
        return "Fehler: GROQ_API_KEY Umgebungsvariable nicht gesetzt.", 0

    try:
        # Build system message with memory context
        system_content = "Du bist ein hilfreicher Assistent. Antworte kurz und prägnant auf Deutsch. Halte deine Antworten unter 3 Sätzen."

        memory_count = 0
        if use_memory and SHODH_API_KEY:
            # Recall relevant memories
            memories = shodh_recall(text, limit=3)
            memory_count = len(memories)
            memory_context = format_memories_for_context(memories)
            if memory_context:
                system_content += f"\n\n{memory_context}"

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_content}]

        # Add recent conversation history
        for exchange in conversation_history[-MAX_HISTORY:]:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["assistant"]})

        # Add current user message
        messages.append({"role": "user", "content": text})

        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=200,
        )
        response = chat_completion.choices[0].message.content

        # Store in conversation history
        conversation_history.append({"user": text, "assistant": response})
        if len(conversation_history) > MAX_HISTORY:
            conversation_history = conversation_history[-MAX_HISTORY:]

        # Store in SHODH memory (async, don't block)
        if use_memory and SHODH_API_KEY:
            try:
                shodh_remember(
                    f"Frage: {text}\nAntwort: {response}",
                    memory_type="Conversation",
                    tags=["ghome-assistant", "voice"]
                )
            except:
                pass  # Don't fail if memory storage fails

        return response, memory_count
    except Exception as e:
        return f"Fehler bei der Verarbeitung: {str(e)}", 0

async def generate_tts_audio(text, output_file):
    """Generate TTS audio using Edge TTS."""
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(output_file)

def text_to_speech(text):
    """Convert text to speech and return audio file path."""
    filename = f"assistant_{uuid.uuid4().hex[:8]}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    
    # Run async TTS
    asyncio.run(generate_tts_audio(text, filepath))
    
    return filename, filepath

@app.route('/api/assistant/health')
def assistant_health():
    """Check if Voice Assistant is available."""
    if not groq_client:
        return jsonify({"api_available": False, "error": "GROQ_API_KEY not set"})
    try:
        # Test Groq connection
        test = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": "test"}],
            model="llama-3.3-70b-versatile",
            max_tokens=5,
        )

        # Check SHODH memory status
        memory_available = False
        memory_count = 0
        if SHODH_API_KEY:
            try:
                response = requests.get(
                    f"{SHODH_URL}/api/stats",
                    headers={"Authorization": f"Bearer {SHODH_API_KEY}"},
                    timeout=3
                )
                if response.status_code == 200:
                    stats = response.json()
                    memory_available = True
                    memory_count = stats.get("total_memories", 0)
            except:
                pass

        return jsonify({
            "api_available": True,
            "llm": "Groq (llama-3.3-70b)",
            "tts": "Edge TTS",
            "voice": TTS_VOICE,
            "memory_available": memory_available,
            "memory_count": memory_count
        })
    except Exception as e:
        return jsonify({"api_available": False, "error": str(e)})

@app.route('/api/assistant/chat', methods=['POST'])
def assistant_chat():
    """
    Chat with voice output to Google Home.
    Uses Groq for LLM and Edge TTS for speech synthesis.
    """
    global current_source
    data = request.get_json() or {}
    text = data.get('text', '')
    use_memory = data.get('use_memory', True)

    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    try:
        # Get LLM response from Groq (with memory context)
        response_text, memory_count = get_groq_response(text, use_memory=use_memory)

        # Generate TTS audio
        filename, filepath = text_to_speech(response_text)

        # Build audio URL
        audio_url = f"http://{LOCAL_IP}:{LOCAL_PORT}/audio/{filename}"

        # Stop current playback
        run_catt("stop")
        time.sleep(0.5)

        # Cast audio to Google Home
        stdout, stderr, code = run_catt("cast", audio_url)

        if code == 0:
            current_source = {"type": "assistant", "name": "Voice Assistant"}

        return jsonify({
            "success": code == 0,
            "input": text,
            "response": response_text,
            "audio_url": audio_url,
            "memory_count": memory_count,
            "message": "Antwort wird abgespielt" if code == 0 else stderr
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/assistant/chat/text', methods=['POST'])
def assistant_chat_text():
    """
    Chat with text response only (no audio).
    """
    data = request.get_json() or {}
    text = data.get('text', '')
    use_memory = data.get('use_memory', True)

    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    try:
        response_text, memory_count = get_groq_response(text, use_memory=use_memory)
        return jsonify({
            "success": True,
            "input": text,
            "response": response_text,
            "memory_count": memory_count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/assistant/chat/browser', methods=['POST'])
def assistant_chat_browser():
    """
    Chat with audio response for browser playback.
    Returns audio URL without casting to Google Home.
    """
    data = request.get_json() or {}
    text = data.get('text', '')
    use_memory = data.get('use_memory', True)

    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    try:
        # Get LLM response from Groq (with memory context)
        response_text, memory_count = get_groq_response(text, use_memory=use_memory)

        # Generate TTS audio
        filename, filepath = text_to_speech(response_text)

        # Return audio URL for browser playback
        audio_url = f"/audio/{filename}"

        return jsonify({
            "success": True,
            "input": text,
            "response": response_text,
            "audio_url": audio_url,
            "memory_count": memory_count,
            "message": response_text
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
