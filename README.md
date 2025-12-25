# Google Home Web Controller

A Flask web application to control Google Home / Chromecast devices via [catt](https://github.com/skorokithakis/catt).

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

### Voice Assistant Integration
Optional integration with a separate Voice Assistant API:
- Text-based chat interface
- Text-to-speech output to Google Home
- Requires separate Voice Assistant server

## Requirements

- Python 3.8+
- Flask, Requests
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
pip install flask requests

# Install catt (system-wide or via pipx)
pipx install catt
# or: pip install catt
```

## Configuration

Edit `app.py` to configure your setup:

```python
# Your Google Home device name (as shown in Google Home app)
DEVICE = "Familienzimmer"

# Your server's IP (for network access)
LOCAL_IP = "10.0.1.70"
LOCAL_PORT = 5000

# Optional: Voice Assistant API endpoint
VOICE_ASSISTANT_API = "http://10.0.1.39:5001"
```

### Adding Radio Stations

Edit the `RADIO_STATIONS` dictionary in `app.py`:

```python
RADIO_STATIONS = {
    "Station Name": "https://stream-url.com/stream",
    # ...
}
```

### Adding YouTube Favorites

Edit the `YOUTUBE_FAVORITES` dictionary in `app.py`:

```python
YOUTUBE_FAVORITES = {
    "Video Name": "https://www.youtube.com/watch?v=VIDEO_ID",
    # ...
}
```

**Note**: Live streams don't work (DRM protected). Use regular videos only.

## Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python app.py
```

Open in browser:
- Local: http://localhost:5000
- Network: http://YOUR_IP:5000

## Production Deployment (Pi-Hole)

The app is deployed on Pi-Hole server (10.0.1.56) with systemd and lighttpd reverse proxy.

### Access URL
- **http://ghome.home** (from any device using Pi-Hole DNS)

### Systemd Service
```bash
# Service file: /etc/systemd/system/ghome-web.service
sudo systemctl status ghome-web
sudo systemctl restart ghome-web
```

### Lighttpd Reverse Proxy
Config: `/etc/lighttpd/conf-enabled/20-ghome.conf`
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
hosts = [ "10.0.1.56 ghome.home", "10.0.1.56 ghome" ]
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

### Voice Assistant (optional)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/assistant/health` | GET | Check API availability |
| `/api/assistant/chat` | POST | Chat with audio output |
| `/api/assistant/chat/text` | POST | Chat with text response only |

## Project Structure

```
ghome-web/
├── app.py              # Flask backend
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
- The Voice Assistant API runs on a separate server
- Check if the API is reachable at the configured endpoint

## License

MIT
