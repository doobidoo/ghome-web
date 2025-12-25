"""Google Home Web Controller - Configuration"""

# Device name for catt commands
DEVICE = "Familienzimmer"

# Edge TTS Voice
TTS_VOICE = "de-CH-LeniNeural"  # Swiss German female voice

# Assistant Persona
ASSISTANT_PERSONA = """Du bist Leni, e Schwiizer Assistäntin.

Persönlichkeit:
- Kompetänt und diräkt
- Du duezisch alli
- Kei Höflichkeitsfloskle, chum uf de Punkt
- Churz und knapp, keis Gschwafel

Sproch:
- Schwiizerdütsch (Züridütsch)
- Max. 1-2 Sätz pro Antwort
- Für Sprochussgab optimiert (kei Sonderzeiche, kei Liste)

Antwort churz und hilf diräkt."""

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

# Local server settings
LOCAL_IP = "10.0.1.56"
LOCAL_PORT = 5000

# Conversation history
MAX_HISTORY = 5
