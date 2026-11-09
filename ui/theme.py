"""
Pixel Art 2D Theme, Procedural Pixel Avatar Generator, and 8-bit Web Audio / Particle FX Engine
for Griductive UI.
Provides authentic 8-bit / 16-bit styling, 3D card flip animations, zero-jank CSS transitions,
multi-track Chiptune BGM synthesizer, sound effects (SFX), and pixel particle bursts.
"""
import hashlib
import re
from typing import Dict, Tuple


PIXEL_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap');

:root {
    --bg-main: #141622;
    --bg-panel: #22273e;
    --card-down: #303956;
    --card-border-down: #566c86;
    --card-innocent-border: #38b764;
    --card-criminal-border: #e43b44;
    --highlight-border: #ffcd75;
    --pixel-black: #0b0c14;
    --pixel-white: #f4f4f4;
    --gold: #ef7d57;
    --cyan: #29adff;
}

html, body {
    background-color: var(--bg-main);
    background-image:
        radial-gradient(#293252 1px, transparent 1px),
        radial-gradient(#1f2640 1px, var(--bg-main) 1px);
    background-size: 24px 24px;
    background-position: 0 0, 12px 12px;
    color: var(--pixel-white);
    font-family: 'VT323', monospace;
    font-size: 20px;
    margin: 0;
    padding: 0;
    image-rendering: pixelated;
    user-select: none;
    overflow-x: hidden;
}

.pixel-title {
    font-family: 'Press Start 2P', monospace;
    font-size: 15px;
    color: #ffcd75;
    text-shadow: 3px 3px 0px #000;
    letter-spacing: 1px;
}

.pixel-subtitle {
    font-family: 'Press Start 2P', monospace;
    font-size: 9px;
    color: #a7f070;
    letter-spacing: 1px;
}

.pixel-panel {
    background-color: var(--bg-panel);
    border: 4px solid var(--pixel-black);
    box-shadow: 4px 4px 0px #000;
    padding: 10px 12px;
}

.pixel-btn {
    font-family: 'Press Start 2P', monospace !important;
    font-size: 9px !important;
    padding: 6px 10px !important;
    border: 3px solid #000 !important;
    border-radius: 0px !important;
    box-shadow: 3px 3px 0px #000 !important;
    cursor: pointer;
    background-color: #4a5c78 !important;
    color: #fff !important;
    transition: filter 0.1s, transform 0.06s, box-shadow 0.06s;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}

.pixel-btn:hover {
    filter: brightness(1.18);
}

.pixel-btn:active {
    transform: translate(2px, 2px);
    box-shadow: 1px 1px 0px #000 !important;
}

.pixel-btn-chap-active {
    background-color: #ffcd75 !important;
    color: #000 !important;
    border: 3px solid #fff !important;
}

.pixel-btn-innocent {
    background-color: #38b764 !important;
    color: #000 !important;
}

.pixel-btn-criminal {
    background-color: #e43b44 !important;
    color: #fff !important;
}

.pixel-btn-hint {
    background-color: #ffcd75 !important;
    color: #000 !important;
}

.pixel-btn-solve {
    background-color: #29adff !important;
    color: #000 !important;
}

.pixel-btn-restart {
    background-color: #ef7d57 !important;
    color: #fff !important;
}

/* Fixed-Height Status Bar to prevent ANY layout shift on feedback */
.detective-status-bar {
    height: 48px;
    min-height: 48px;
    max-height: 48px;
    width: 100%;
    background-color: #141828;
    border: 3px solid #000;
    box-shadow: inset 2px 2px 0px #000;
    padding: 2px 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-sizing: border-box;
    transition: background-color 0.2s, border-color 0.2s;
    overflow: hidden;
}

.status-bar-info {
    border-color: #29adff;
    background-color: #162238;
}

.status-bar-accepted {
    border-color: #38b764;
    background-color: #142e24;
}

.status-bar-warning {
    border-color: #ffcd75;
    background-color: #332b14;
}

.status-bar-error {
    border-color: #e43b44;
    background-color: #38161b;
}

/* Card Styles - Fixed dimensions so flipping NEVER shifts neighbor cards */
.grid-card {
    position: relative;
    width: 166px;
    height: 216px;
    min-height: 216px;
    max-height: 216px;
    background-color: var(--card-down);
    border: 4px solid var(--card-border-down);
    border-radius: 0px !important;
    box-shadow: 4px 4px 0px #000;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 5px 6px;
    box-sizing: border-box;
    cursor: pointer;
    transform-style: preserve-3d;
    backface-visibility: hidden;
    transition: transform 0.16s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.16s, box-shadow 0.16s, background-color 0.2s;
}

.grid-card:hover {
    transform: translateY(-3px);
    box-shadow: 5px 7px 0px #000;
}

.grid-card.card-revealed-innocent {
    background: linear-gradient(180deg, #ffffff 0%, #eafaf0 100%);
    border: 4px solid var(--card-innocent-border);
    color: #1a1c2c;
}

.grid-card.card-revealed-criminal {
    background: linear-gradient(180deg, #ffffff 0%, #fdecec 100%);
    border: 4px solid var(--card-criminal-border);
    color: #1a1c2c;
}

.grid-card.card-highlighted {
    border: 4px solid var(--highlight-border) !important;
    box-shadow: 0 0 14px rgba(255, 205, 117, 0.85), 4px 4px 0px #000 !important;
}

.grid-card.card-active-clue {
    outline: 3px dashed #29adff;
    outline-offset: 2px;
}

.grid-card.card-hint-target {
    border: 4px solid #73eff7 !important;
    box-shadow: 0 0 18px #29adff, 4px 4px 0px #000 !important;
    animation: hint-beacon 0.9s infinite alternate ease-in-out;
}

@keyframes hint-beacon {
    0% { filter: brightness(1.0); transform: translateY(0px); }
    100% { filter: brightness(1.22); transform: translateY(-4px); }
}

/* 3D Card Flip Reveal Animation */
.card-flip-reveal {
    animation: pixel-flip-3d 0.52s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes pixel-flip-3d {
    0% {
        transform: perspective(700px) rotateY(90deg) scale(0.88);
        filter: brightness(1.8);
    }
    60% {
        transform: perspective(700px) rotateY(-8deg) scale(1.05);
        filter: brightness(1.2);
    }
    100% {
        transform: perspective(700px) rotateY(0deg) scale(1.0);
        filter: brightness(1.0);
    }
}

/* Shake animation for errors */
.shake-animation {
    animation: pixel-shake 0.42s ease-in-out;
}

@keyframes pixel-shake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-7px) rotate(-1.5deg); }
    40%, 80% { transform: translateX(7px) rotate(1.5deg); }
}

/* Avatar subtle idle bobbing */
.avatar-wrapper {
    transition: transform 0.15s ease;
}
.grid-card:hover .avatar-wrapper {
    transform: scale(1.1);
}

.badge-tag {
    font-family: 'Press Start 2P', monospace;
    font-size: 8px;
    padding: 2px 5px;
    border: 2px solid #000;
}

.badge-coord {
    background-color: #1a1c2c;
    color: #ffcd75;
}

.badge-innocent {
    background-color: #38b764;
    color: #000;
    box-shadow: 2px 2px 0px #000;
}

.badge-criminal {
    background-color: #e43b44;
    color: #fff;
    box-shadow: 2px 2px 0px #000;
}

/* Clue Box on Card - Never clips top or bottom of long clues */
.card-clue-box {
    background-color: #eef2f7;
    border: 2px solid #1a1c2c;
    box-shadow: 2px 2px 0px #1a1c2c;
    padding: 4px 5px;
    margin-top: 2px;
    width: 100%;
    height: 82px;
    min-height: 82px;
    max-height: 82px;
    flex-shrink: 0;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    box-sizing: border-box;
    font-family: 'VT323', monospace;
    font-size: 15px;
    line-height: 1.15;
    text-align: center;
    color: #1a1c2c;
    word-break: break-word;
    display: block;
}

.card-clue-box::-webkit-scrollbar {
    width: 5px;
}

.card-clue-box::-webkit-scrollbar-thumb {
    background-color: #566c86;
}

.card-clue-box:hover {
    background-color: #fff8d6;
    border-color: #ef7d57;
}

/* Highlighted keywords inside clue text */
.kw-crim { color: #d91e2a; font-weight: bold; }
.kw-inno { color: #1e8742; font-weight: bold; }
.kw-coord { color: #1b56b3; font-weight: bold; }
.kw-num { color: #7a2299; font-weight: bold; }

/* Metrics and Log styling */
.metric-box {
    background-color: #141828;
    border: 2px solid #566c86;
    padding: 4px 7px;
    font-family: 'Press Start 2P', monospace;
    font-size: 8px;
    color: #29adff;
}

.metric-box span {
    color: #ffcd75;
}

.clue-list-box {
    background-color: #141824;
    border: 3px solid #000;
    box-shadow: inset 2px 2px 0px #000;
    padding: 8px;
    height: 190px;
    min-height: 190px;
    max-height: 190px;
    overflow-y: auto;
    width: 100%;
    box-sizing: border-box;
}

.clue-list-item {
    background-color: #20263b;
    border: 2px solid #3c486b;
    padding: 4px 8px;
    margin-bottom: 5px;
    cursor: pointer;
    font-family: 'VT323', monospace;
    font-size: 17px;
    color: #f4f4f4;
    transition: background-color 0.1s, border-color 0.1s;
}

.clue-list-item:hover, .clue-list-item.active-clue-item {
    background-color: #2d3859;
    border-color: #ffcd75;
}

.trace-log {
    background-color: #12141f;
    border: 3px solid #000;
    box-shadow: inset 2px 2px 0px #000;
    padding: 8px;
    font-family: 'VT323', monospace;
    font-size: 17px;
    color: #a7f070;
    height: 195px;
    min-height: 195px;
    max-height: 195px;
    overflow-y: auto;
    width: 100%;
    box-sizing: border-box;
}

.trace-entry {
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px dashed #333c57;
}

.trace-entry .step-tag {
    color: #ffcd75;
    font-weight: bold;
}

.trace-entry .verdict-crim {
    color: #e43b44;
    font-weight: bold;
}

.trace-entry .verdict-inno {
    color: #38b764;
    font-weight: bold;
}

/* Pixel Particle Burst */
.pixel-particle {
    position: fixed;
    width: 7px;
    height: 7px;
    pointer-events: none;
    z-index: 9999;
    box-shadow: 1px 1px 0px #000;
}
"""


AUDIO_AND_FX_JS = """
<script>
window.GriductiveFX = (function() {
    let ctx = null;
    let bgmPlaying = false;
    let bgmTrack = 'noir';
    let bgmVolume = 0.35;
    let sfxVolume = 0.65;
    let bgmTimer = null;
    let stepIndex = 0;

    // 4 Chiptune Detective Tracks (Note frequencies in Hz)
    const TRACKS = {
        noir: {
            tempo: 260,
            wave: 'triangle',
            bassWave: 'sawtooth',
            melody: [220, 0, 261.63, 246.94, 220, 0, 196, 220, 261.63, 0, 329.63, 293.66, 261.63, 246.94, 220, 0],
            bass:   [110, 110, 130.81, 130.81, 98, 98, 110, 110, 130.81, 130.81, 164.81, 146.83, 130.81, 123.47, 110, 110]
        },
        cyber: {
            tempo: 185,
            wave: 'square',
            bassWave: 'triangle',
            melody: [329.63, 392, 440, 392, 523.25, 493.88, 440, 392, 349.23, 440, 523.25, 440, 392, 349.23, 329.63, 293.66],
            bass:   [164.81, 164.81, 196, 196, 220, 220, 196, 196, 174.61, 174.61, 220, 220, 196, 174.61, 164.81, 146.83]
        },
        trial: {
            tempo: 165,
            wave: 'square',
            bassWave: 'sawtooth',
            melody: [293.66, 293.66, 0, 349.23, 392, 0, 440, 0, 466.16, 440, 392, 349.23, 392, 0, 293.66, 0],
            bass:   [146.83, 0, 146.83, 174.61, 196, 0, 220, 0, 233.08, 220, 196, 174.61, 196, 146.83, 146.83, 0]
        },
        chill: {
            tempo: 320,
            wave: 'sine',
            bassWave: 'triangle',
            melody: [261.63, 329.63, 392, 493.88, 440, 392, 329.63, 0, 293.66, 349.23, 440, 523.25, 493.88, 392, 329.63, 0],
            bass:   [130.81, 0, 196, 0, 164.81, 0, 130.81, 0, 146.83, 0, 220, 0, 196, 0, 130.81, 0]
        }
    };

    function ensureCtx() {
        if (!ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) ctx = new AudioCtx();
        }
        if (ctx && ctx.state === 'suspended') {
            ctx.resume();
        }
        return ctx;
    }

    function playTone(freq, durationMs, type, gainVal, delayMs = 0) {
        if (gainVal <= 0.001 || !freq) return;
        const c = ensureCtx();
        if (!c) return;
        const start = c.currentTime + (delayMs / 1000.0);
        const dur = durationMs / 1000.0;

        const osc = c.createOscillator();
        const gain = c.createGain();
        osc.type = type || 'square';
        osc.frequency.setValueAtTime(freq, start);

        gain.gain.setValueAtTime(0.0001, start);
        gain.gain.linearRampToValueAtTime(gainVal, start + 0.015);
        gain.gain.exponentialRampToValueAtTime(0.0001, start + dur);

        osc.connect(gain);
        gain.connect(c.destination);
        osc.start(start);
        osc.stop(start + dur + 0.02);
    }

    function scheduleBGM() {
        if (bgmTimer) {
            clearInterval(bgmTimer);
            bgmTimer = null;
        }
        if (!bgmPlaying) return;
        const track = TRACKS[bgmTrack] || TRACKS.noir;
        bgmTimer = setInterval(() => {
            if (!bgmPlaying || bgmVolume <= 0.001) return;
            const idx = stepIndex % track.melody.length;
            const mFreq = track.melody[idx];
            const bFreq = track.bass[idx];
            if (mFreq > 0) {
                playTone(mFreq, track.tempo * 0.85, track.wave, bgmVolume * 0.14, 0);
            }
            if (bFreq > 0) {
                playTone(bFreq, track.tempo * 0.9, track.bassWave, bgmVolume * 0.10, 0);
            }
            stepIndex++;
        }, track.tempo);
    }

    const api = {
        toggleBGM: function(forceState) {
            ensureCtx();
            bgmPlaying = (typeof forceState === 'boolean') ? forceState : !bgmPlaying;
            scheduleBGM();
            return bgmPlaying;
        },
        setBGMTrack: function(trackName) {
            bgmTrack = trackName;
            stepIndex = 0;
            if (bgmPlaying) scheduleBGM();
        },
        setBGMVolume: function(val) {
            bgmVolume = Math.max(0, Math.min(1, parseFloat(val) || 0));
        },
        setSFXVolume: function(val) {
            sfxVolume = Math.max(0, Math.min(1, parseFloat(val) || 0));
        },
        playSFX: function(kind, baseDelay = 0) {
            if (sfxVolume <= 0.001) return;
            ensureCtx();
            const v = sfxVolume * 0.28;
            const d0 = baseDelay || 0;
            if (kind === 'press_inno') {
                // Crisp, bright stamp sound when pressing INNO button
                playTone(698.46, 42, 'triangle', v * 0.95, d0);
                playTone(987.77, 55, 'square', v * 0.80, d0 + 32);
            } else if (kind === 'press_crim') {
                // Sharp, heavy gavel/handcuff lock sound when pressing CRIM button
                playTone(370.00, 42, 'sawtooth', v * 0.95, d0);
                playTone(246.94, 60, 'square', v * 0.90, d0 + 32);
            } else if (kind === 'select') {
                playTone(587.33, 55, 'square', v * 0.7, d0);
                playTone(880.0, 65, 'square', v * 0.6, d0 + 45);
            } else if (kind === 'button') {
                playTone(440.0, 45, 'triangle', v * 0.65, d0);
            } else if (kind === 'flip_inno') {
                playTone(523.25, 80, 'square', v, d0);
                playTone(659.25, 80, 'square', v, d0 + 65);
                playTone(783.99, 110, 'square', v, d0 + 130);
                playTone(1046.50, 180, 'triangle', v * 1.1, d0 + 200);
            } else if (kind === 'flip_crim') {
                playTone(392.00, 80, 'sawtooth', v, d0);
                playTone(466.16, 80, 'sawtooth', v, d0 + 65);
                playTone(587.33, 110, 'square', v, d0 + 130);
                playTone(783.99, 200, 'square', v * 1.1, d0 + 200);
            } else if (kind === 'not_provable') {
                playTone(240.0, 120, 'sawtooth', v, d0);
                playTone(195.0, 170, 'sawtooth', v, d0 + 130);
            } else if (kind === 'contradicted') {
                playTone(165.0, 140, 'sawtooth', v * 1.2, d0);
                playTone(130.81, 140, 'sawtooth', v * 1.2, d0 + 120);
                playTone(110.0, 240, 'sawtooth', v * 1.2, d0 + 240);
            } else if (kind === 'hint') {
                playTone(659.25, 70, 'sine', v, d0);
                playTone(880.0, 70, 'sine', v, d0 + 70);
                playTone(1174.66, 150, 'triangle', v, d0 + 140);
            } else if (kind === 'victory') {
                const notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 1046.50];
                const durs  = [100,    100,    100,    220,     100,    360];
                let delay = d0;
                for (let i = 0; i < notes.length; i++) {
                    playTone(notes[i], durs[i], 'square', v * 1.15, delay);
                    delay += durs[i] * 0.85;
                }
            }
        },
        celebrateCard: function(cardId, role) {
            const el = document.getElementById(cardId);
            if (!el) return;
            el.classList.remove('card-flip-reveal', 'shake-animation');
            void el.offsetWidth; // trigger reflow on single card only
            el.classList.add('card-flip-reveal');

            // Spawn pixel particles around the card
            const rect = el.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const colors = (role === 'INNOCENT')
                ? ['#38b764', '#a7f070', '#ffcd75', '#ffffff']
                : ['#e43b44', '#ef7d57', '#ffcd75', '#ffffff'];

            for (let i = 0; i < 16; i++) {
                const p = document.createElement('div');
                p.className = 'pixel-particle';
                p.style.backgroundColor = colors[i % colors.length];
                p.style.left = cx + 'px';
                p.style.top = cy + 'px';
                document.body.appendChild(p);

                const angle = (Math.PI * 2 * i) / 16 + (Math.random() * 0.3);
                const dist = 45 + Math.random() * 55;
                const tx = Math.cos(angle) * dist;
                const ty = Math.sin(angle) * dist - 15;

                p.animate([
                    { transform: 'translate(0px, 0px) scale(1.2)', opacity: 1 },
                    { transform: `translate(${tx}px, ${ty}px) scale(0.2)`, opacity: 0 }
                ], {
                    duration: 520 + Math.random() * 200,
                    easing: 'cubic-bezier(0.16, 1, 0.3, 1)'
                }).onfinish = () => p.remove();
            }
        },
        shakeCard: function(cardId) {
            const el = document.getElementById(cardId);
            if (!el) return;
            el.classList.remove('shake-animation');
            void el.offsetWidth;
            el.classList.add('shake-animation');
        }
    };

    // Instant client-side tactile feedback on pointerdown (0ms latency + unlocks AudioContext)
    document.addEventListener('pointerdown', function(e) {
        ensureCtx();
        const target = e.target;
        if (!target || !target.closest) return;
        if (target.closest('.verdict-btn-inno')) {
            api.playSFX('press_inno', 0);
        } else if (target.closest('.verdict-btn-crim')) {
            api.playSFX('press_crim', 0);
        } else if (target.closest('.pixel-btn')) {
            api.playSFX('button', 0);
        }
    }, true);

    return api;
})();
</script>
"""


def format_clue_html(text: str, dark_bg: bool = False) -> str:
    """
    Formats clue text with colored keyword spans for readability,
    matching the original web detective game style.
    """
    if not text:
        return "<i>No clue</i>"
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    escaped = re.sub(
        r"(\([A-E][1-5]\)|Row\s+[1-5]|Column\s+[A-E]|the 4 corners|common neighbors)",
        r'<span class="kw-coord" style="' + ("color:#73eff7;" if dark_bg else "") + r'">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"\b(Criminals?|CRIMINAL)\b",
        r'<span class="kw-crim" style="' + ("color:#ff6b72;" if dark_bg else "") + r'">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"\b(Innocents?|INNOCENT)\b",
        r'<span class="kw-inno" style="' + ("color:#68e390;" if dark_bg else "") + r'">\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"\b(SAME|DIFFERENT|NO|ODD|EVEN|MORE|FEWER|Equal|Exactly\s+\d+|At\s+least\s+\d+|At\s+most\s+\d+)\b",
        r'<span class="kw-num" style="' + ("color:#ffcd75;" if dark_bg else "") + r'">\1</span>',
        escaped,
    )
    return escaped


def generate_pixel_avatar_svg(name: str, occupation: str, size: int = 44) -> str:
    """
    Deterministically generates a 16x16 Pixel Art SVG avatar based on character
    name and occupation. Completely offline with zero external image dependencies.
    """
    h = int(hashlib.md5(f"{name}_{occupation}".encode()).hexdigest()[:8], 16)

    skin_tones = ["#ffdbac", "#f1c27d", "#e0ac69", "#c68642", "#8d5524"]
    hair_colors = ["#2c1b18", "#4a3728", "#8d4a2b", "#b55239", "#e6be8a", "#666666", "#dcdcdc"]
    shirt_colors = ["#3b5dc9", "#e43b44", "#38b764", "#ef7d57", "#b13e53", "#73eff7", "#9370db"]

    skin = skin_tones[h % len(skin_tones)]
    hair = hair_colors[(h >> 3) % len(hair_colors)]
    shirt = shirt_colors[(h >> 6) % len(shirt_colors)]

    pixels: Dict[Tuple[int, int], str] = {}

    for x in range(5, 11):
        pixels[(x, 3)] = hair
    for x in range(4, 12):
        pixels[(x, 4)] = hair

    for y in range(5, 10):
        for x in range(5, 11):
            pixels[(x, y)] = skin

    pixels[(4, 5)] = hair
    pixels[(11, 5)] = hair
    pixels[(4, 6)] = hair
    pixels[(11, 6)] = hair

    pixels[(6, 6)] = "#1a1c2c"
    pixels[(9, 6)] = "#1a1c2c"
    pixels[(7, 7)] = "#b87d4b"
    pixels[(7, 9)] = "#b13e53"
    pixels[(8, 9)] = "#b13e53"

    for x in range(6, 10):
        pixels[(x, 10)] = skin

    for y in range(11, 16):
        for x in range(3, 13):
            pixels[(x, y)] = shirt

    pixels[(7, 11)] = "#ffffff"
    pixels[(8, 11)] = "#ffffff"
    pixels[(7, 12)] = "#000000"
    pixels[(8, 12)] = "#000000"

    occ_lower = occupation.lower()
    if "detective" in occ_lower:
        f_color = "#4a3728"
        for x in range(3, 13):
            pixels[(x, 4)] = f_color
        for x in range(5, 11):
            pixels[(x, 3)] = "#e43b44"
            pixels[(x, 2)] = f_color
    elif "guard" in occ_lower or "police" in occ_lower:
        p_color = "#1f3c88"
        for x in range(4, 12):
            pixels[(x, 3)] = p_color
            pixels[(x, 2)] = p_color
        for x in range(4, 13):
            pixels[(x, 4)] = "#000000"
        pixels[(8, 3)] = "#ffcd75"
    elif "cook" in occ_lower or "baker" in occ_lower:
        w_color = "#ffffff"
        for x in range(5, 11):
            pixels[(x, 1)] = w_color
            pixels[(x, 2)] = w_color
            pixels[(x, 3)] = w_color
            pixels[(x, 4)] = w_color
        pixels[(4, 2)] = w_color
        pixels[(11, 2)] = w_color
    elif "doctor" in occ_lower or "nurse" in occ_lower:
        pixels[(7, 3)] = "#ffffff"
        pixels[(8, 3)] = "#ffffff"
        pixels[(7, 4)] = "#e43b44"
        pixels[(8, 4)] = "#e43b44"
    elif "clerk" in occ_lower or "lawyer" in occ_lower or "banker" in occ_lower:
        pixels[(5, 6)] = "#000000"
        pixels[(6, 6)] = "#73eff7"
        pixels[(7, 6)] = "#000000"
        pixels[(8, 6)] = "#000000"
        pixels[(9, 6)] = "#73eff7"
        pixels[(10, 6)] = "#000000"
    elif "pilot" in occ_lower:
        pixels[(5, 5)] = "#ffcd75"
        pixels[(6, 5)] = "#29adff"
        pixels[(7, 5)] = "#ffcd75"
        pixels[(8, 5)] = "#ffcd75"
        pixels[(9, 5)] = "#29adff"
        pixels[(10, 5)] = "#ffcd75"

    rects = []
    for (x, y), color in pixels.items():
        rects.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{color}"/>')

    svg_content = "".join(rects)
    svg_str = (
        f'<div class="avatar-wrapper">'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
        f'width="{size}" height="{size}" style="shape-rendering: crispEdges; image-rendering: pixelated;">'
        f'{svg_content}</svg></div>'
    )
    return svg_str
