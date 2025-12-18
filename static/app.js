// Google Home Web Controller - Frontend JS

const API = {
    info: '/api/info',
    play: '/api/play',
    pause: '/api/pause',
    stop: '/api/stop',
    volume: (level) => `/api/volume/${level}`,
    volumeup: '/api/volumeup',
    volumedown: '/api/volumedown',
    skip: '/api/skip'
};

// DOM Elements
const elements = {
    statusDot: document.getElementById('statusDot'),
    albumArt: document.getElementById('albumArt'),
    noArt: document.getElementById('noArt'),
    trackTitle: document.getElementById('trackTitle'),
    trackArtist: document.getElementById('trackArtist'),
    trackAlbum: document.getElementById('trackAlbum'),
    currentTime: document.getElementById('currentTime'),
    duration: document.getElementById('duration'),
    progress: document.getElementById('progress'),
    btnPlayPause: document.getElementById('btnPlayPause'),
    iconPlay: document.getElementById('iconPlay'),
    iconPause: document.getElementById('iconPause'),
    btnStop: document.getElementById('btnStop'),
    btnSkip: document.getElementById('btnSkip'),
    volumeSlider: document.getElementById('volumeSlider'),
    volumeValue: document.getElementById('volumeValue'),
    btnVolUp: document.getElementById('btnVolUp'),
    btnVolDown: document.getElementById('btnVolDown'),
    appName: document.getElementById('appName')
};

let isPlaying = false;
let updateInterval = null;

// Format seconds to MM:SS
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Update UI with player info
function updateUI(info) {
    // Status dot
    if (info.playing) {
        elements.statusDot.classList.add('active');
    } else {
        elements.statusDot.classList.remove('active');
    }

    // Track info
    if (info.title) {
        elements.trackTitle.textContent = info.title;
    } else if (info.player_state === 'IDLE') {
        elements.trackTitle.textContent = 'Nicht aktiv';
    } else {
        elements.trackTitle.textContent = 'Wiedergabe aktiv';
    }

    elements.trackArtist.textContent = info.artist || '';
    elements.trackAlbum.textContent = info.album || '';

    // Album art
    if (info.image_url) {
        elements.albumArt.src = info.image_url;
        elements.albumArt.classList.add('visible');
        elements.noArt.style.display = 'none';
    } else {
        elements.albumArt.classList.remove('visible');
        elements.noArt.style.display = 'flex';
    }

    // Progress
    elements.currentTime.textContent = formatTime(info.current_time);
    elements.duration.textContent = formatTime(info.duration);

    if (info.duration > 0) {
        const percent = (info.current_time / info.duration) * 100;
        elements.progress.style.width = `${percent}%`;
    } else {
        elements.progress.style.width = '0%';
    }

    // Play/Pause button
    isPlaying = info.playing;
    if (isPlaying) {
        elements.iconPlay.style.display = 'none';
        elements.iconPause.style.display = 'block';
    } else {
        elements.iconPlay.style.display = 'block';
        elements.iconPause.style.display = 'none';
    }

    // Volume
    if (info.volume !== undefined) {
        elements.volumeSlider.value = info.volume;
        elements.volumeValue.textContent = `${info.volume}%`;
    }

    // App name
    elements.appName.textContent = info.app || '';
}

// Fetch player info
async function fetchInfo() {
    try {
        const response = await fetch(API.info);
        const info = await response.json();
        updateUI(info);
    } catch (error) {
        console.error('Error fetching info:', error);
    }
}

// Send POST request
async function sendCommand(url) {
    try {
        const response = await fetch(url, { method: 'POST' });
        const result = await response.json();
        // Refresh info after command
        setTimeout(fetchInfo, 300);
        return result;
    } catch (error) {
        console.error('Error sending command:', error);
        return { success: false };
    }
}

// Event Listeners
elements.btnPlayPause.addEventListener('click', () => {
    if (isPlaying) {
        sendCommand(API.pause);
    } else {
        sendCommand(API.play);
    }
});

elements.btnStop.addEventListener('click', () => {
    sendCommand(API.stop);
});

elements.btnSkip.addEventListener('click', () => {
    sendCommand(API.skip);
});

elements.btnVolUp.addEventListener('click', () => {
    sendCommand(API.volumeup);
});

elements.btnVolDown.addEventListener('click', () => {
    sendCommand(API.volumedown);
});

let volumeTimeout = null;
elements.volumeSlider.addEventListener('input', (e) => {
    const value = e.target.value;
    elements.volumeValue.textContent = `${value}%`;

    // Debounce volume changes
    clearTimeout(volumeTimeout);
    volumeTimeout = setTimeout(() => {
        sendCommand(API.volume(value));
    }, 100);
});

// Progress bar click to seek
document.querySelector('.progress-bar').addEventListener('click', (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const duration = parseFloat(elements.duration.textContent.split(':').reduce((a, b) => a * 60 + parseFloat(b), 0));

    if (duration > 0) {
        const seekTime = Math.floor(percent * duration);
        const mins = Math.floor(seekTime / 60);
        const secs = seekTime % 60;
        fetch(`/api/seek/${mins}:${secs.toString().padStart(2, '0')}`, { method: 'POST' })
            .then(() => setTimeout(fetchInfo, 500));
    }
});

// Initial fetch and start auto-refresh
fetchInfo();
updateInterval = setInterval(fetchInfo, 3000);

// Visibility API - pause updates when tab is hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        clearInterval(updateInterval);
    } else {
        fetchInfo();
        updateInterval = setInterval(fetchInfo, 3000);
    }
});
