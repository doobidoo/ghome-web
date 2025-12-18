# Google Home Web Controller

A simple Flask web app to control Google Home / Chromecast devices via [catt](https://github.com/skorokithakis/catt).

![Dark Theme UI](https://img.shields.io/badge/theme-dark-121212)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Flask](https://img.shields.io/badge/flask-3.x-green)

## Features

- **Now Playing**: Track title, artist, album, album art
- **Playback Controls**: Play, Pause, Stop, Skip
- **Volume Control**: Slider + buttons
- **Progress Bar**: Click to seek
- **Auto-Refresh**: Updates every 3 seconds
- **Dark Theme**: Spotify-inspired design

## Requirements

- Python 3.8+
- Flask
- [catt](https://github.com/skorokithakis/catt) installed and configured

## Installation

```bash
# Clone the repo
git clone https://github.com/doobidoo/ghome-web.git
cd ghome-web

# Install dependencies
pip install flask
pipx install catt

# Configure your device in app.py
DEVICE = "Your-Device-Name"
```

## Usage

```bash
python3 app.py
```

Open http://localhost:5000 in your browser.

## API Endpoints

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

## License

MIT
