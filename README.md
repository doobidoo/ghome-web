# Google Home Web Controller

A Flask web application to control Google Home / Chromecast devices via [catt](https://github.com/skorokithakis/catt), with an integrated AI Voice Assistant.

![Dark Theme UI](https://img.shields.io/badge/theme-dark-121212)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)

## Features

### Playback Control
- **Now Playing**: Track title, artist, album, album art
- **Playback Controls**: Play, Pause, Stop, Skip
- **Volume Control**: Slider + buttons (+/- 10)
- **Progress Bar**: Visual progress with click-to-seek
- **Auto-Refresh**: Updates every 3 seconds
- **Dark Theme**: Spotify-inspired design

### Radio Stations
Pre-configured streaming radio stations:
- **Swiss**: SRF 1, SRF 2 Kultur, SRF 3, SRF 4 News, Radio Swiss Jazz/Classic/Pop
- **Austrian**: FM4, Ö1, Ö3
- **German**: Bayern 3, WDR 2, NDR 2, 1LIVE, Klassik Radio
- **International**: Lounge FM

### YouTube Favorites
Quick access to curated YouTube videos:
- Worship compilations (Hillsong, etc.)
- Jazz playlists (Smooth Jazz, Jazz Fusion)

### Voice Assistant "Leni"
Integrated AI assistant with Swiss personality:
- **LLM**: Groq (Llama 3.3 70B)
- **TTS**: Edge TTS (de-CH-LeniNeural - Swiss German voice)
- **STT**: Web Speech API (browser-based)
- **Memory**: SHODH Cloudflare semantic memory
- **Persona**: Professional Swiss assistant

#### Memory Features
- Semantic recall of previous conversations
- Intelligent trigger patterns for storage:
  - "Merke dir: ..." / "Wichtig: ..." - explicit storage
  - Casual greetings are skipped automatically
- Visual feedback: Memory stored (disk icon), Memories used (brain icon)

## Requirements

- Python 3.8+
- Flask, Requests, Groq, Edge-TTS
- [catt](https://github.com/skorokithakis/catt) installed and configured
- Google Home / Chromecast device on the same network

## Installation

```bash
# Clone the repo
git clone https://github.com/doobidoo/ghome-web.git
cd ghome-web

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask requests groq edge-tts

# Install catt (system-wide or via pipx)
pipx install catt
# or: pip install catt
```

## Configuration

All configuration is in `config.py`:

```python
# Device name (as shown in Google Home app)
DEVICE = "Familienzimmer"

# Voice Assistant
TTS_VOICE = "de-CH-LeniNeural"  # Swiss German female voice
ASSISTANT_PERSONA = """Du bist Leni, eine professionelle Schweizer Assistentin..."""

# Network settings
LOCAL_IP = "10.0.1.56"
LOCAL_PORT = 5000

# Media
RADIO_STATIONS = { ... }
YOUTUBE_FAVORITES = { ... }
```

### Environment Variables

Set these for the Voice Assistant:

```bash
export GROQ_API_KEY="your-groq-api-key"
export SHODH_CLOUDFLARE_URL="https://your-worker.workers.dev"
export SHODH_CLOUDFLARE_API_KEY="your-api-key"
```

### Customizing Leni's Personality

Edit `ASSISTANT_PERSONA` in `config.py`:

```python
ASSISTANT_PERSONA = """Du bist Leni, eine professionelle Schweizer Assistentin.

Persönlichkeit:
- Kompetent, effizient und zuverlässig
- Höflich und respektvoll, aber nicht übertrieben förmlich
- Präzise Antworten ohne unnötiges Geplauder
- Gelegentlich dezente Schweizer Höflichkeitsformen (Grüezi, Merci)

Sprachstil:
- Klares Hochdeutsch mit leichtem Schweizer Einschlag
- Kurze, prägnante Sätze (max. 2-3 Sätze pro Antwort)
- Professionell aber warmherzig
- Für Sprachausgabe optimiert (keine Sonderzeichen, Listen vermeiden)

Du hilfst bei Fragen, merkst dir wichtige Informationen und gibst hilfreiche Antworten."""
```

### Adding Radio Stations / YouTube Favorites

Edit the dictionaries in `config.py`:

```python
RADIO_STATIONS = {
    "Station Name": "https://stream-url.com/stream",
}

YOUTUBE_FAVORITES = {
    "Video Name": "https://www.youtube.com/watch?v=VIDEO_ID",
}
```

**Note**: YouTube live streams don't work (DRM protected). Use regular videos only.

## Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export GROQ_API_KEY="your-key"

# Start the server
python app.py
```

Open in browser:
- Local: http://localhost:5000
- Network: http://YOUR_IP:5000

## Memory Trigger Patterns

The Voice Assistant uses intelligent patterns to decide what to store:

### Explicit Storage Triggers
- "Merke dir: ..." / "Merk dir: ..."
- "Speichere: ..." / "Speicher: ..."
- "Wichtig: ..." / "Notiz: ..." / "Info: ..."
- "Vergiss nicht: ..."
- "Remember: ..."

### Skip Patterns (not stored)
- Greetings: "Hallo", "Hi", "Grüezi", etc.
- Casual: "Wie geht's", "Danke", "OK"
- Short responses: "Ja", "Nein"

### Recall Triggers
- "Was weisst du über..."
- "Erinnerst du dich an..."
- "Was habe ich dir gesagt über..."

## Production Deployment

For production, deploy with systemd and a reverse proxy (nginx/lighttpd).

### Systemd Service

Create `/etc/systemd/system/ghome-web.service`:
```ini
[Unit]
Description=Google Home Web Controller
After=network.target

[Service]
Type=simple
User=hkr
WorkingDirectory=/home/hkr/ghome-web
Environment=PATH=/home/hkr/ghome-web/venv/bin:/usr/bin
Environment=GROQ_API_KEY=your-key
Environment=SHODH_CLOUDFLARE_URL=https://your-worker.workers.dev
Environment=SHODH_CLOUDFLARE_API_KEY=your-key
ExecStart=/home/hkr/ghome-web/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ghome-web
sudo systemctl start ghome-web
```

### Reverse Proxy (Lighttpd)

Config for `/etc/lighttpd/conf-enabled/20-ghome.conf`:
```
$HTTP["host"] =~ "^ghome\.home$|^ghome$" {
    auth.require = ()
    proxy.server = ( "" => ( ( "host" => "127.0.0.1", "port" => 5000 ) ) )
}
```

### Pi-Hole v6 DNS Configuration

**Important**: Pi-Hole v6 does NOT use `/etc/dnsmasq.d/` or `/etc/pihole/custom.list`.

Edit `/etc/pihole/pihole.toml`:
```toml
hosts = [ "YOUR_SERVER_IP ghome.home", "YOUR_SERVER_IP ghome" ]
```

Then restart: `sudo systemctl restart pihole-FTL`

### Why .home instead of .local?
systemd-resolved routes `.local` domains to mDNS (Avahi), not DNS. Using `.home` ensures proper DNS resolution via Pi-Hole.

## API Endpoints

### Playback Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/info` | GET | Current playback status |
| `/api/play` | POST | Resume playback |
| `/api/pause` | POST | Pause playback |
| `/api/stop` | POST | Stop playback |
| `/api/skip` | POST | Skip current track |
| `/api/volume/<0-100>` | POST | Set volume |
| `/api/volumeup` | POST | Volume +10 |
| `/api/volumedown` | POST | Volume -10 |
| `/api/seek/<MM:SS>` | POST | Seek to position |

### Radio

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/radio/stations` | GET | List all stations |
| `/api/radio/play/<station>` | POST | Play a station |

### YouTube

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/youtube/list` | GET | List all favorites |
| `/api/youtube/play/<name>` | POST | Play a video |

### Voice Assistant

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/assistant/health` | GET | Check API availability + memory status |
| `/api/assistant/chat` | POST | Chat with audio output to Google Home |
| `/api/assistant/chat/text` | POST | Chat with text response only |
| `/api/assistant/chat/browser` | POST | Chat with audio for browser playback |

**Response format:**
```json
{
  "success": true,
  "input": "user question",
  "response": "assistant answer",
  "memory_count": 3,
  "memory_stored": true
}
```

## Project Structure

```
ghome-web/
├── app.py              # Flask backend
├── config.py           # Configuration (persona, stations, settings)
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main UI template
└── static/
    ├── app.js          # Frontend JavaScript
    └── style.css       # Styles (dark theme)
```

## Troubleshooting

### "Device not found"
- Ensure your Google Home is on the same network
- Check device name: `catt scan`
- Test manually: `catt -d "Device Name" info`

### Radio/YouTube not playing
- Some streams require specific codecs
- YouTube live streams don't work (DRM)
- Check catt output for errors

### Voice Assistant offline
- Check GROQ_API_KEY environment variable
- Verify Groq API is reachable
- Check logs: `journalctl -u ghome-web -f`

### Memory not working
- Check SHODH_CLOUDFLARE_URL and SHODH_CLOUDFLARE_API_KEY
- Test API: `curl -H "Authorization: Bearer $KEY" $URL/api/stats`

## License

MIT
