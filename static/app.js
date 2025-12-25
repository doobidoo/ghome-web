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

function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateUI(info) {
    if (info.playing) {
        elements.statusDot.classList.add('active');
    } else {
        elements.statusDot.classList.remove('active');
    }

    if (info.title) {
        elements.trackTitle.textContent = info.title;
    } else if (info.player_state === 'IDLE') {
        elements.trackTitle.textContent = 'Nicht aktiv';
    } else {
        elements.trackTitle.textContent = 'Wiedergabe aktiv';
    }

    elements.trackArtist.textContent = info.artist || '';
    elements.trackAlbum.textContent = info.album || '';

    if (info.image_url) {
        elements.albumArt.src = info.image_url;
        elements.albumArt.classList.add('visible');
        elements.noArt.style.display = 'none';
    } else {
        elements.albumArt.classList.remove('visible');
        elements.noArt.style.display = 'flex';
    }

    elements.currentTime.textContent = formatTime(info.current_time);
    elements.duration.textContent = formatTime(info.duration);

    if (info.duration > 0) {
        const percent = (info.current_time / info.duration) * 100;
        elements.progress.style.width = `${percent}%`;
    } else {
        elements.progress.style.width = '0%';
    }

    isPlaying = info.playing;
    if (isPlaying) {
        elements.iconPlay.style.display = 'none';
        elements.iconPause.style.display = 'block';
    } else {
        elements.iconPlay.style.display = 'block';
        elements.iconPause.style.display = 'none';
    }

    if (info.volume !== undefined) {
        elements.volumeSlider.value = info.volume;
        elements.volumeValue.textContent = `${info.volume}%`;
    }

    elements.appName.textContent = info.app || '';
}

async function fetchInfo() {
    try {
        const response = await fetch(API.info);
        const info = await response.json();
        updateUI(info);
    } catch (error) {
        console.error('Error fetching info:', error);
    }
}

async function sendCommand(url) {
    try {
        const response = await fetch(url, { method: 'POST' });
        const result = await response.json();
        setTimeout(fetchInfo, 300);
        return result;
    } catch (error) {
        console.error('Error sending command:', error);
        return { success: false };
    }
}

elements.btnPlayPause.addEventListener('click', () => {
    sendCommand(isPlaying ? API.pause : API.play);
});

elements.btnStop.addEventListener('click', () => sendCommand(API.stop));
elements.btnSkip.addEventListener('click', () => sendCommand(API.skip));
elements.btnVolUp.addEventListener('click', () => sendCommand(API.volumeup));
elements.btnVolDown.addEventListener('click', () => sendCommand(API.volumedown));

let volumeTimeout = null;
elements.volumeSlider.addEventListener('input', (e) => {
    const value = e.target.value;
    elements.volumeValue.textContent = `${value}%`;
    clearTimeout(volumeTimeout);
    volumeTimeout = setTimeout(() => sendCommand(API.volume(value)), 100);
});

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

fetchInfo();
updateInterval = setInterval(fetchInfo, 3000);

document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        clearInterval(updateInterval);
    } else {
        fetchInfo();
        updateInterval = setInterval(fetchInfo, 3000);
    }
});

// Radio
const radioGrid = document.getElementById('radioGrid');

async function loadRadioStations() {
    try {
        const response = await fetch('/api/radio/stations');
        const data = await response.json();
        radioGrid.innerHTML = '';
        data.stations.forEach(station => {
            const btn = document.createElement('button');
            btn.className = 'radio-btn';
            btn.textContent = station;
            btn.addEventListener('click', () => playRadio(station));
            radioGrid.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading stations:', error);
    }
}

async function playRadio(station) {
    document.querySelectorAll('.yt-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.radio-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === station);
    });

    try {
        const response = await fetch(`/api/radio/play/${encodeURIComponent(station)}`, { method: 'POST' });
        const result = await response.json();
        if (result.success) setTimeout(fetchInfo, 1500);
    } catch (error) {
        console.error('Error playing radio:', error);
    }
}

loadRadioStations();

// YouTube
const youtubeGrid = document.getElementById('youtubeGrid');

async function loadYouTubeVideos() {
    try {
        const response = await fetch('/api/youtube/list');
        const data = await response.json();
        youtubeGrid.innerHTML = '';
        data.videos.forEach(name => {
            const btn = document.createElement('button');
            btn.className = 'yt-btn';
            btn.textContent = name;
            btn.addEventListener('click', () => playYouTube(name));
            youtubeGrid.appendChild(btn);
        });
    } catch (error) {
        console.error('Error loading YouTube:', error);
    }
}

async function playYouTube(name) {
    document.querySelectorAll('.radio-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.yt-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === name);
    });

    try {
        const response = await fetch(`/api/youtube/play/${encodeURIComponent(name)}`, { method: 'POST' });
        const result = await response.json();
        if (result.success) setTimeout(fetchInfo, 2000);
    } catch (error) {
        console.error('Error playing YouTube:', error);
    }
}

loadYouTubeVideos();

// ==================== Voice Assistant ====================

const assistantElements = {
    input: document.getElementById('assistantInput'),
    btnSend: document.getElementById('btnAssistantSend'),
    btnMic: document.getElementById('btnAssistantMic'),
    micIcon: document.getElementById('micIcon'),
    micActiveIcon: document.getElementById('micActiveIcon'),
    response: document.getElementById('chatResponse'),
    indicator: document.getElementById('assistantIndicator'),
    statusText: document.getElementById('assistantStatusText'),
    autoPlayToggle: document.getElementById('autoPlayToggle'),
    btnOutputBrowser: document.getElementById('btnOutputBrowser'),
    btnOutputGHome: document.getElementById('btnOutputGHome'),
    silenceDuration: document.getElementById('silenceDuration'),
    silenceValue: document.getElementById('silenceValue'),
    browserAudio: document.getElementById('browserAudio')
};

let assistantOnline = false;
let outputTarget = 'browser'; // 'browser' or 'ghome'

// ==================== Output Target ====================

function loadOutputTarget() {
    const saved = localStorage.getItem('ghome_output_target');
    if (saved) outputTarget = saved;
    updateOutputButtons();
}

function setOutputTarget(target) {
    outputTarget = target;
    localStorage.setItem('ghome_output_target', target);
    updateOutputButtons();
}

function updateOutputButtons() {
    assistantElements.btnOutputBrowser.classList.toggle('active', outputTarget === 'browser');
    assistantElements.btnOutputGHome.classList.toggle('active', outputTarget === 'ghome');
}

assistantElements.btnOutputBrowser.addEventListener('click', () => setOutputTarget('browser'));
assistantElements.btnOutputGHome.addEventListener('click', () => setOutputTarget('ghome'));
loadOutputTarget();

// ==================== Speech Recognition ====================

let recognition = null;
let isListening = false;
let silenceTimer = null;
let lastSpeechTime = null;
let finalTranscript = '';

function getSilenceDuration() {
    return parseFloat(assistantElements.silenceDuration.value) * 1000;
}

function loadSilencePreference() {
    const saved = localStorage.getItem('ghome_silence_duration');
    if (saved !== null) {
        assistantElements.silenceDuration.value = saved;
        assistantElements.silenceValue.textContent = saved + 's';
    }
}

function saveSilencePreference() {
    const value = assistantElements.silenceDuration.value;
    localStorage.setItem('ghome_silence_duration', value);
    assistantElements.silenceValue.textContent = value + 's';
}

loadSilencePreference();
assistantElements.silenceDuration.addEventListener('input', saveSilencePreference);

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'de-DE';

    recognition.onstart = () => {
        isListening = true;
        finalTranscript = '';
        lastSpeechTime = Date.now();
        assistantElements.btnMic.classList.add('listening');
        assistantElements.micIcon.style.display = 'none';
        assistantElements.micActiveIcon.style.display = 'block';
        assistantElements.input.placeholder = 'Ich höre zu...';
        startSilenceDetection();
    };

    recognition.onend = () => {
        stopSilenceDetection();
        if (finalTranscript.trim() && isListening) {
            assistantElements.input.value = finalTranscript;
            setTimeout(() => {
                if (assistantElements.input.value.trim()) smartSend();
            }, 100);
        }
        isListening = false;
        assistantElements.btnMic.classList.remove('listening');
        assistantElements.micIcon.style.display = 'block';
        assistantElements.micActiveIcon.style.display = 'none';
        assistantElements.input.placeholder = 'Frag mich etwas...';
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        lastSpeechTime = Date.now();
        assistantElements.input.value = (finalTranscript + interimTranscript).trim();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopSilenceDetection();
        isListening = false;
        assistantElements.btnMic.classList.remove('listening');
        assistantElements.micIcon.style.display = 'block';
        assistantElements.micActiveIcon.style.display = 'none';
        assistantElements.input.placeholder = 'Frag mich etwas...';

        if (event.error === 'not-allowed') {
            assistantElements.response.className = 'chat-response error';
            assistantElements.response.textContent = 'Mikrofon-Zugriff verweigert.';
        } else if (event.error === 'no-speech' && finalTranscript.trim()) {
            assistantElements.input.value = finalTranscript;
            smartSend();
        }
    };
} else {
    if (assistantElements.btnMic) assistantElements.btnMic.style.display = 'none';
}

function startSilenceDetection() {
    stopSilenceDetection();
    silenceTimer = setInterval(() => {
        if (lastSpeechTime && (Date.now() - lastSpeechTime) >= getSilenceDuration()) {
            if (recognition && isListening) recognition.stop();
        }
    }, 100);
}

function stopSilenceDetection() {
    if (silenceTimer) {
        clearInterval(silenceTimer);
        silenceTimer = null;
    }
}

function toggleSpeechRecognition() {
    if (!recognition) {
        assistantElements.response.className = 'chat-response error';
        assistantElements.response.textContent = 'Spracherkennung nicht unterstützt.';
        return;
    }
    if (isListening) {
        recognition.stop();
    } else {
        finalTranscript = '';
        assistantElements.input.value = '';
        recognition.start();
    }
}

if (assistantElements.btnMic) {
    assistantElements.btnMic.addEventListener('click', () => {
        unlockAudio();
        toggleSpeechRecognition();
    });
}

// ==================== Auto-Play ====================

function loadAutoPlayPreference() {
    const saved = localStorage.getItem('ghome_autoplay_tts');
    if (saved !== null) assistantElements.autoPlayToggle.checked = saved === 'true';
}

function saveAutoPlayPreference() {
    localStorage.setItem('ghome_autoplay_tts', assistantElements.autoPlayToggle.checked);
}

loadAutoPlayPreference();
assistantElements.autoPlayToggle.addEventListener('change', saveAutoPlayPreference);

// ==================== Health Check ====================

async function checkAssistantHealth() {
    try {
        const response = await fetch('/api/assistant/health');
        const data = await response.json();
        assistantOnline = data.api_available;

        if (assistantOnline) {
            assistantElements.indicator.classList.add('online');
            assistantElements.indicator.classList.remove('offline');
            const llm = data.llm || 'Groq';
            const ttsVoice = data.voice || 'Edge TTS';
            const stt = SpeechRecognition ? 'Web Speech API' : '-';
            let statusText = `LLM: ${llm} | STT: ${stt} | TTS: ${ttsVoice}`;
            if (data.memory_available) {
                statusText += ` | Mem: ${data.memory_count}`;
            }
            assistantElements.statusText.textContent = statusText;
        } else {
            assistantElements.indicator.classList.remove('online');
            assistantElements.indicator.classList.add('offline');
            assistantElements.statusText.textContent = 'Offline';
        }
    } catch (error) {
        assistantOnline = false;
        assistantElements.indicator.classList.remove('online');
        assistantElements.indicator.classList.add('offline');
        assistantElements.statusText.textContent = 'Offline';
    }
}

// ==================== Chat Functions ====================

async function sendTextMessage(text) {
    if (!text.trim()) return;

    assistantElements.response.className = 'chat-response loading';
    assistantElements.response.innerHTML = 'Denke nach...';
    setButtonsDisabled(true);

    try {
        const response = await fetch('/api/assistant/chat/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await response.json();

        if (data.success) {
            showResponse(text, data.response, data.memory_count || 0, data.memory_stored || false);
            assistantElements.input.value = '';
        } else {
            showError(data.error || 'Fehler bei der Verarbeitung');
        }
    } catch (error) {
        showError('Verbindungsfehler');
    }

    setButtonsDisabled(false);
}

async function sendWithVoice(text) {
    if (!text.trim()) return;

    const toGoogleHome = outputTarget === 'ghome';
    const endpoint = toGoogleHome ? '/api/assistant/chat' : '/api/assistant/chat/browser';

    assistantElements.response.className = 'chat-response loading';
    assistantElements.response.innerHTML = toGoogleHome ? 'Sende an Google Home...' : 'Generiere Audio...';
    setButtonsDisabled(true);

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await response.json();

        if (data.success) {
            showResponse(text, data.response || data.message, data.memory_count || 0, data.memory_stored || false);

            if (!toGoogleHome && data.audio_url) {
                playBrowserAudio(data.audio_url);
            }

            if (toGoogleHome) {
                document.querySelectorAll('.radio-btn, .yt-btn').forEach(btn => btn.classList.remove('active'));
            }
        } else {
            showError(data.error || 'Fehler bei der Verarbeitung');
        }
    } catch (error) {
        showError('Verbindungsfehler');
    }

    setButtonsDisabled(false);
    assistantElements.input.value = '';
}

function showResponse(question, answer, memoryCount = 0, memoryStored = false) {
    assistantElements.response.className = 'chat-response';
    let memoryInfo = '';
    if (memoryStored) {
        memoryInfo = ' <span style="color: #4ade80; font-size: 0.7rem;" title="Gespeichert">💾</span>';
    }
    if (memoryCount > 0) {
        memoryInfo += ` <span style="color: var(--accent); font-size: 0.7rem;">(${memoryCount} 🧠)</span>`;
    }
    assistantElements.response.innerHTML =
        '<div class="user-message">Du: ' + escapeHtml(question) + '</div>' +
        '<div class="assistant-message">' + escapeHtml(answer) + memoryInfo + '</div>';
}

function showError(message) {
    assistantElements.response.className = 'chat-response error';
    assistantElements.response.textContent = message;
}

function setButtonsDisabled(disabled) {
    assistantElements.btnSend.disabled = disabled;
    assistantElements.btnMic.disabled = disabled;
}

// iOS Safari audio unlock - must be called from user gesture
let audioUnlocked = false;

function unlockAudio() {
    if (audioUnlocked) return;
    const audio = assistantElements.browserAudio;
    // Play silent audio to unlock
    audio.src = 'data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABhgC7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7u7//////////////////////////////////////////////////////////////////8AAAAATGF2YzU4LjEzAAAAAAAAAAAAAAAAJAAAAAAAAAAAAYYoRwmHAAAAAAD/+9DEAAAIAANIAAAAgAADSAAAAATEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//tQxB4AAADSAAAAAAAAANIAAAAATEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVU=';
    audio.volume = 0.01;
    audio.play().then(() => {
        audio.pause();
        audio.volume = 1;
        audioUnlocked = true;
        console.log('Audio unlocked for iOS Safari');
    }).catch(() => {});
}

function playBrowserAudio(audioUrl) {
    const audio = assistantElements.browserAudio;
    audio.src = audioUrl;
    audio.load(); // Force reload for iOS

    const playPromise = audio.play();
    if (playPromise !== undefined) {
        playPromise.catch(err => {
            console.error('Audio playback failed:', err);
            // Show manual play button as fallback
            showAudioFallback(audioUrl);
        });
    }
}

function showAudioFallback(audioUrl) {
    const responseEl = assistantElements.response;
    const playBtn = document.createElement('button');
    playBtn.textContent = '▶ Audio abspielen';
    playBtn.style.cssText = 'margin-top:8px;padding:8px 16px;background:var(--accent);color:#000;border:none;border-radius:4px;cursor:pointer;';
    playBtn.onclick = () => {
        assistantElements.browserAudio.src = audioUrl;
        assistantElements.browserAudio.play();
        playBtn.remove();
    };
    responseEl.appendChild(playBtn);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function smartSend() {
    const text = assistantElements.input.value;
    if (assistantElements.autoPlayToggle.checked) {
        sendWithVoice(text);
    } else {
        sendTextMessage(text);
    }
}

assistantElements.btnSend.addEventListener('click', () => {
    unlockAudio();
    smartSend();
});
assistantElements.input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        unlockAudio();
        smartSend();
    }
});

checkAssistantHealth();
setInterval(checkAssistantHealth, 30000);
