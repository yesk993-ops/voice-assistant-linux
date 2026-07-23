"""
Web Server for Linux Voice Assistant
Serves a futuristic J.A.R.V.I.S. / Iron Man style Web UI and exposes REST APIs.
"""

import os
import sys
import io
import logging
import wave
import base64
import tempfile
from flask import Flask, jsonify, request, render_template_string
from pathlib import Path

# Add project root to path so imports work correctly
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from voice_assistant.main import VoiceAssistant
from voice_assistant.modules.response_formatter import ResponseType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Voice Assistant in API-only mode
logger.info("Initializing Voice Assistant backend for Web UI...")
assistant = VoiceAssistant()

# HTML template for the Iron Man/J.A.R.V.I.S HUD Web UI
HUD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>J.A.R.V.I.S. HUD - System Control</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-glow: #00f0ff;
            --primary-dim: #005f73;
            --primary-dark: #0a192f;
            --accent-orange: #ff5714;
            --accent-green: #9ef01a;
            --bg-color: #020813;
            --panel-bg: rgba(10, 25, 47, 0.6);
            --panel-border: rgba(0, 240, 255, 0.3);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 50% 50%, rgba(0, 95, 115, 0.15) 0%, transparent 80%),
                linear-gradient(rgba(18, 18, 18, 0.5) 50%, rgba(0, 0, 0, 0.25) 50%),
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 100%, 100% 4px, 6px 100%;
            color: #fff;
            font-family: 'Share Tech Mono', monospace;
            height: 100vh;
            overflow: hidden;
            padding: 20px;
            display: grid;
            grid-template-columns: 320px 1fr 320px;
            grid-template-rows: 80px 1fr 120px;
            gap: 20px;
        }

        /* Scanline effect overlay */
        body::before {
            content: " ";
            display: block;
            position: absolute;
            top: 0; left: 0; bottom: 0; right: 0;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            z-index: 9999;
            background-size: 100% 2px, 3px 100%;
            pointer-events: none;
            opacity: 0.3;
        }

        /* Ambient audio visualizer bars on left/right edges */
        .hud-border-glow {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            border: 1px solid rgba(0, 240, 255, 0.15);
            pointer-events: none;
            box-shadow: inset 0 0 40px rgba(0, 240, 255, 0.05);
            z-index: -1;
        }

        /* HEADER */
        header {
            grid-column: 1 / -1;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--panel-border);
            background: var(--panel-bg);
            padding: 0 20px;
            border-radius: 4px;
            position: relative;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
        }

        header::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 5%;
            width: 90%;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--primary-glow), transparent);
        }

        .logo-section h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 24px;
            font-weight: 900;
            letter-spacing: 3px;
            color: var(--primary-glow);
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
        }

        .logo-section span {
            font-size: 10px;
            color: var(--primary-dim);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .system-status-indicator {
            display: flex;
            gap: 20px;
            font-size: 12px;
        }

        .stat-badge {
            background: rgba(0, 240, 255, 0.05);
            border: 1px solid rgba(0, 240, 255, 0.2);
            padding: 5px 12px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stat-badge span.dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--accent-green);
            animation: pulse 1.5s infinite;
        }

        /* PANELS - GENERAL */
        .hud-panel {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 4px;
            padding: 15px;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.05);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .hud-panel::before {
            content: '';
            position: absolute;
            top: 0; left: 0;
            width: 12px; height: 12px;
            border-top: 2px solid var(--primary-glow);
            border-left: 2px solid var(--primary-glow);
        }

        .hud-panel::after {
            content: '';
            position: absolute;
            bottom: 0; right: 0;
            width: 12px; height: 12px;
            border-bottom: 2px solid var(--primary-glow);
            border-right: 2px solid var(--primary-glow);
        }

        .panel-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            color: var(--primary-glow);
            letter-spacing: 2px;
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(0, 240, 255, 0.2);
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }

        /* LEFT SIDEBAR: System Status */
        .left-sidebar {
            grid-column: 1;
            grid-row: 2;
            gap: 15px;
            display: flex;
            flex-direction: column;
        }

        .gauge-container {
            margin-bottom: 15px;
        }

        .gauge-label {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #a5f3fc;
            margin-bottom: 5px;
        }

        .bar-outer {
            width: 100%;
            height: 10px;
            background: rgba(0, 240, 255, 0.05);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
        }

        .bar-inner {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--primary-dim), var(--primary-glow));
            box-shadow: 0 0 8px var(--primary-glow);
            transition: width 0.5s ease-out;
        }

        /* CENTER PANEL: J.A.R.V.I.S. Core (Arc Reactor) */
        .center-hud {
            grid-column: 2;
            grid-row: 2;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        /* ARC REACTOR VISUALIZER */
        .arc-reactor-wrapper {
            position: relative;
            width: 280px;
            height: 280px;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
        }

        .arc-ring {
            position: absolute;
            border-radius: 50%;
            border: 2px dashed rgba(0, 240, 255, 0.3);
            transition: all 0.3s ease;
        }

        .ring-outer {
            width: 260px;
            height: 260px;
            border: 1px solid rgba(0, 240, 255, 0.15);
            border-top: 4px solid var(--primary-glow);
            border-bottom: 4px solid var(--primary-glow);
            animation: spin-clockwise 10s linear infinite;
        }

        .ring-middle {
            width: 210px;
            height: 210px;
            border: 2px dashed rgba(0, 240, 255, 0.4);
            border-left: 4px solid var(--accent-orange);
            animation: spin-counter 7s linear infinite;
        }

        .ring-inner {
            width: 160px;
            height: 160px;
            border: 3px double rgba(0, 240, 255, 0.5);
            border-right: 4px solid var(--primary-glow);
            animation: spin-clockwise 4s linear infinite;
        }

        .core-glow {
            position: absolute;
            width: 80px;
            height: 80px;
            background: radial-gradient(circle, rgba(0, 240, 255, 1) 0%, rgba(0, 95, 115, 0.8) 40%, rgba(2, 8, 19, 0) 70%);
            border-radius: 50%;
            box-shadow: 0 0 35px rgba(0, 240, 255, 0.8);
            animation: core-pulse 2s infinite ease-in-out;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            border: 1px solid rgba(0, 240, 255, 0.6);
        }

        .core-glow::after {
            content: 'MIC';
            font-size: 11px;
            font-weight: bold;
            color: #fff;
            font-family: 'Orbitron', sans-serif;
            text-shadow: 0 0 5px #000;
        }

        /* Arc reactor state animations */
        .state-listening .ring-outer {
            border: 4px solid var(--accent-orange) !important;
            animation: spin-clockwise 2s linear infinite;
            box-shadow: 0 0 20px var(--accent-orange);
        }
        .state-listening .core-glow {
            background: radial-gradient(circle, rgba(255, 87, 20, 1) 0%, rgba(180, 50, 5, 0.8) 40%, transparent 70%);
            box-shadow: 0 0 35px var(--accent-orange);
        }

        .state-processing .ring-middle {
            border: 4px solid #fff !important;
            animation: spin-counter 1s linear infinite;
        }

        .state-speaking .ring-inner {
            border-color: var(--accent-green) !important;
            box-shadow: 0 0 25px var(--accent-green);
        }

        /* TEXT CONSOLE RESPONSE DISPLAY */
        .response-terminal {
            width: 100%;
            max-width: 600px;
            background: rgba(2, 8, 19, 0.85);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 4px;
            padding: 15px;
            height: 120px;
            overflow-y: auto;
            font-family: 'Share Tech Mono', monospace;
            font-size: 14px;
            color: var(--primary-glow);
            box-shadow: inset 0 0 15px rgba(0, 240, 255, 0.1);
        }

        .terminal-prompt {
            color: var(--accent-orange);
            margin-bottom: 5px;
        }

        .terminal-text {
            line-height: 1.4;
            color: #e0f2fe;
            margin-bottom: 5px;
        }

        /* RIGHT SIDEBAR: Command Reference & Logs */
        .right-sidebar {
            grid-column: 3;
            grid-row: 2;
            gap: 15px;
            display: flex;
            flex-direction: column;
        }

        .log-list {
            list-style: none;
            font-size: 11px;
            color: #94a3b8;
            max-height: 180px;
            overflow-y: auto;
            line-height: 1.5;
        }

        .log-item {
            border-bottom: 1px solid rgba(0, 240, 255, 0.1);
            padding: 4px 0;
            display: flex;
            justify-content: space-between;
        }

        .log-time {
            color: var(--primary-glow);
        }

        .suggestions-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
            max-height: 250px;
            overflow-y: auto;
        }

        .suggestion-btn {
            background: rgba(0, 240, 255, 0.05);
            border: 1px solid rgba(0, 240, 255, 0.2);
            color: #93c5fd;
            padding: 6px 10px;
            font-size: 11px;
            text-align: left;
            border-radius: 2px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Share Tech Mono', monospace;
        }

        .suggestion-btn:hover {
            background: rgba(0, 240, 255, 0.15);
            border-color: var(--primary-glow);
            color: #fff;
            transform: translateX(5px);
        }

        /* BOTTOM INPUT PANEL */
        footer {
            grid-column: 1 / -1;
            grid-row: 3;
            border: 1px solid var(--panel-border);
            background: var(--panel-bg);
            padding: 15px;
            border-radius: 4px;
            display: flex;
            gap: 15px;
            align-items: center;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.1);
        }

        .input-wrapper {
            position: relative;
            flex-grow: 1;
            display: flex;
        }

        .hud-input {
            width: 100%;
            background: rgba(2, 8, 19, 0.8);
            border: 1px solid var(--panel-border);
            color: #fff;
            font-family: 'Share Tech Mono', monospace;
            font-size: 16px;
            padding: 12px 20px;
            border-radius: 4px;
            outline: none;
            transition: border-color 0.3s;
            box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.1);
        }

        .hud-input:focus {
            border-color: var(--primary-glow);
            box-shadow: inset 0 0 15px rgba(0, 240, 255, 0.2), 0 0 10px rgba(0, 240, 255, 0.2);
        }

        .voice-control-btn {
            background: linear-gradient(135deg, var(--primary-dim), var(--primary-glow));
            color: var(--primary-dark);
            border: none;
            border-radius: 4px;
            padding: 0 25px;
            font-family: 'Orbitron', sans-serif;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.2s;
            height: 48px;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
        }

        .voice-control-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.7);
            color: #fff;
        }

        .voice-control-btn:active {
            transform: translateY(0);
        }

        /* KEYFRAME ANIMATIONS */
        @keyframes spin-clockwise {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes spin-counter {
            from { transform: rotate(0deg); }
            to { transform: rotate(-360deg); }
        }

        @keyframes core-pulse {
            0% { transform: scale(1); opacity: 0.8; }
            50% { transform: scale(1.05); opacity: 1; box-shadow: 0 0 50px rgba(0, 240, 255, 0.9); }
            100% { transform: scale(1); opacity: 0.8; }
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.5; }
        }

        /* CUSTOM SCROLLBARS */
        ::-webkit-scrollbar {
            width: 4px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(2, 8, 19, 0.5);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--primary-dim);
            border-radius: 2px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary-glow);
        }
    </style>
</head>
<body class="">
    <div class="hud-border-glow"></div>
    
    <!-- HEADER HUD -->
    <header>
        <div class="logo-section">
            <h1>J.A.R.V.I.S.</h1>
            <span>MARK-85 System Core Interface</span>
        </div>
        <div class="system-status-indicator">
            <div class="stat-badge">
                <span class="dot"></span>
                <span>VOICE: READY</span>
            </div>
            <div class="stat-badge">
                <span>INTENT PARSER: 100% ACTIVE</span>
            </div>
        </div>
    </header>

    <!-- LEFT PANEL: SYSTEM HEALTH MONITOR -->
    <div class="hud-panel left-sidebar">
        <div class="panel-header">
            <span>SYS HEALTH</span>
            <span style="font-size: 10px; color: var(--primary-glow)">LIVE</span>
        </div>
        
        <div class="gauge-container">
            <div class="gauge-label">
                <span>CPU UTILIZATION</span>
                <span id="cpu-percent">0.0%</span>
            </div>
            <div class="bar-outer">
                <div class="bar-inner" id="cpu-bar"></div>
            </div>
        </div>

        <div class="gauge-container">
            <div class="gauge-label">
                <span>MEMORY ALLOCATION</span>
                <span id="mem-percent">0.0%</span>
            </div>
            <div class="bar-outer">
                <div class="bar-inner" id="mem-bar"></div>
            </div>
        </div>

        <div class="gauge-container">
            <div class="gauge-label">
                <span>PRIMARY STORAGE (ROOT)</span>
                <span id="disk-percent">0.0%</span>
            </div>
            <div class="bar-outer">
                <div class="bar-inner" id="disk-bar"></div>
            </div>
        </div>

        <div class="gauge-container">
            <div class="gauge-label">
                <span>CORE TEMPERATURE</span>
                <span id="temp-val">N/A</span>
            </div>
            <div class="bar-outer">
                <div class="bar-inner" id="temp-bar" style="width: 45%;"></div>
            </div>
        </div>

        <div class="gauge-container">
            <div class="gauge-label">
                <span>POWER SOURCE / BATTERY</span>
                <span id="battery-percent">N/A</span>
            </div>
            <div class="bar-outer">
                <div class="bar-inner" id="battery-bar" style="width: 100%; background: linear-gradient(90deg, #10b981, #10b981);"></div>
            </div>
        </div>
    </div>

    <!-- CENTER PANEL: HOLO GRAPH & ARC REACTOR -->
    <div class="center-hud">
        <div class="arc-reactor-wrapper" id="arc-reactor">
            <div class="arc-ring ring-outer"></div>
            <div class="arc-ring ring-middle"></div>
            <div class="arc-ring ring-inner"></div>
            <div class="core-glow" id="reactor-core"></div>
        </div>

        <!-- CLI Output / response display -->
        <div class="response-terminal" id="terminal-output">
            <div class="terminal-prompt">J.A.R.V.I.S. CORE v85.12 ONLINE</div>
            <div class="terminal-text">Greetings, Sir. Just say &quot;Jarvis&quot; followed by your command — like &quot;Jarvis, what's the CPU usage?&quot; I'll keep listening for 10 seconds after I respond so you can ask follow-ups.</div>
        </div>
    </div>

    <!-- RIGHT PANEL: COMMAND UTILITY -->
    <div class="hud-panel right-sidebar">
        <div class="panel-header">
            <span>COMMAND SUGGESTIONS</span>
        </div>
        <div class="suggestions-grid">
            <button class="suggestion-btn" onclick="sendQuickCommand('system summary')">⚡ SHOW SYSTEM SUMMARY</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('cpu usage')">📊 CHECK CPU UTILITY</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('memory usage')">💾 CHECK MEMORY LOAD</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('disk usage')">💽 READ STORAGE ALLOCATION</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('show uptime')">⏰ SYSTEM UPTIME</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('list folder')">📂 LIST CURRENT DIRECTORY</button>
            <button class="suggestion-btn" onclick="sendQuickCommand('help')">❓ GENERAL COMMAND HELP</button>
        </div>

        <div class="panel-header" style="margin-top: 15px;">
            <span>DIAGNOSTICS LOG</span>
        </div>
        <ul class="log-list" id="diag-logs">
            <li class="log-item"><span class="log-time">[00:00:01]</span> <span>CORE OK</span></li>
            <li class="log-item"><span class="log-time">[00:00:02]</span> <span>HUD INI</span></li>
        </ul>
    </div>

    <!-- BOTTOM BAR: USER INPUT SECTION -->
    <footer>
        <div class="input-wrapper">
            <input type="text" class="hud-input" id="user-input" placeholder="ACCESS J.A.R.V.I.S. CORE / INPUT COMMAND OR SPEECH..." onkeydown="handleEnter(event)">
        </div>
        <button class="voice-control-btn" id="start-voice-btn">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
                <path d="M19 10v1a7 7 0 0 1-14 0v-1"></path>
                <line x1="12" x2="12" y1="19" y2="22"></line>
            </svg>
            VOICE INPUT
        </button>
    </footer>

    <!-- WEB SPEECH API INTEGRATION — GEMINI-STYLE HANDS-FREE VOICE -->
    <script>
        const terminalOutput = document.getElementById('terminal-output');
        const userInput = document.getElementById('user-input');
        const startVoiceBtn = document.getElementById('start-voice-btn');
        const reactorCore = document.getElementById('reactor-core');
        const arcReactor = document.getElementById('arc-reactor');
        const diagLogs = document.getElementById('diag-logs');

        // ── State ──────────────────────────────────────────────
        let isSpeaking = false;
        let isRecognizing = false;
        let recognitionRestartPending = false;
        let lastTranscriptTime = 0;

        // ── Speech Synthesis ───────────────────────────────────
        const synth = window.speechSynthesis;

        // ── Speech Recognition ─────────────────────────────────
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;

        function createRecognition() {
            if (!SpeechRecognition) {
                console.warn("Web Speech API not supported on this browser.");
                addLog('SYSTEM', 'MIC UNSUPPORTED');
                return null;
            }
            const rec = new SpeechRecognition();
            rec.continuous = true;
            rec.interimResults = true;
            rec.lang = 'en-US';
            rec.maxAlternatives = 1;

            rec.onstart = () => {
                setReactorState('listening');
                addLog('MIC', 'HOT');
                isRecognizing = true;
            };

            rec.onerror = (e) => {
                console.error('SpeechRecognition error:', e.error);
                if (e.error === 'not-allowed') {
                    addLog('MIC', 'BLOCKED — allow mic in browser settings');
                    return;
                }
                // For recoverable errors, restart
                if (e.error !== 'aborted') {
                    scheduleRecognitionRestart();
                }
                isRecognizing = false;
            };

            rec.onend = () => {
                isRecognizing = false;
                // Auto-restart unless interrupted by speaking or manual stop
                if (!recognitionRestartPending && !synth.speaking) {
                    startRecognition();
                } else if (!synth.speaking) {
                    startRecognition();
                    recognitionRestartPending = false;
                }
            };

            rec.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        finalTranscript += result[0].transcript;
                    } else {
                        interimTranscript += result[0].transcript;
                    }
                }

                // Show interim feedback
                if (interimTranscript && !finalTranscript) {
                    showInterim(interimTranscript);
                }

                // Process final transcript
                if (finalTranscript) {
                    const trimmed = finalTranscript.trim().toLowerCase();
                    if (trimmed) {
                        lastTranscriptTime = Date.now();
                        addLog('SPEECH', trimmed);
                        userInput.value = trimmed;
                        showInterim('');
                        
                        // If J.A.R.V.I.S. is speaking, interrupt it
                        if (synth.speaking) {
                            synth.cancel();
                            setReactorState('idle');
                        }
                        
                        // Wake word filtering: only process if starts with "jarvis" or within 10s of last command
                        const now = Date.now();
                        const timeSinceLastCmd = now - (window._lastCommandTime || 0);
                        const inFollowUpWindow = timeSinceLastCmd < 10000 && window._lastCommandTime;
                        const hasWakeWord = trimmed.startsWith('jarvis') || trimmed.startsWith('hey jarvis') || trimmed.startsWith('ok jarvis');
                        
                        if (hasWakeWord) {
                            // Strip wake word and process
                            let cmd = trimmed.replace(/^(hey |ok )?jarvis[,.!?\s]*/i, '').trim();
                            if (cmd) {
                                sendCommand(cmd);
                            } else {
                                // Just "jarvis" — wake up and wait
                                addSpeechTerminal('J.A.R.V.I.S.', 'Yes?');
                            }
                        } else if (inFollowUpWindow) {
                            // In follow-up window, process without wake word
                            sendCommand(trimmed);
                        } else {
                            // No wake word and not in follow-up — ignore (prevents false triggers)
                            showInterim('(waiting for "jarvis"...)');
                        }
                    }
                }
            };

            return rec;
        }

        function startRecognition() {
            if (!recognition) {
                recognition = createRecognition();
            }
            if (!recognition || isRecognizing) return;
            try {
                // Cancel any ongoing speech first
                if (synth.speaking) synth.cancel();
                recognition.start();
            } catch (e) {
                console.warn('Recognition start failed:', e);
                // Chrome sometimes throws if start is called too soon after a previous session
                setTimeout(() => {
                    try { recognition.start(); } catch (ex) { /* ignore */ }
                }, 300);
            }
        }

        function stopRecognition() {
            if (recognition && isRecognizing) {
                try { recognition.stop(); } catch (e) { /* ignore */ }
            }
            isRecognizing = false;
        }

        function scheduleRecognitionRestart() {
            if (recognitionRestartPending) return;
            recognitionRestartPending = true;
            setTimeout(() => {
                recognitionRestartPending = false;
                if (!isRecognizing && !synth.speaking) {
                    startRecognition();
                }
            }, 500);
        }

        // ── Logging ───────────────────────────────────────────
        function addLog(tag, msg) {
            const time = new Date().toLocaleTimeString();
            const li = document.createElement('li');
            li.className = 'log-item';
            li.innerHTML = `<span class="log-time">[${time}]</span> <span>${tag}: ${msg}</span>`;
            diagLogs.insertBefore(li, diagLogs.firstChild);
            if (diagLogs.children.length > 30) {
                diagLogs.removeChild(diagLogs.lastChild);
            }
        }

        // ── Arc Reactor Visual States ─────────────────────────
        function setReactorState(state) {
            arcReactor.className = 'arc-reactor-wrapper';
            if (state !== 'idle') {
                arcReactor.classList.add('state-' + state);
            }
        }

        // ── Interim transcript display ────────────────────────
        let interimEl = null;
        function showInterim(text) {
            if (!interimEl) {
                interimEl = document.createElement('div');
                interimEl.className = 'terminal-text';
                interimEl.style.color = '#94a3b8';
                interimEl.style.fontStyle = 'italic';
                terminalOutput.appendChild(interimEl);
            }
            if (text) {
                interimEl.textContent = '🎤 ' + text;
                terminalOutput.scrollTop = terminalOutput.scrollHeight;
            } else {
                interimEl.remove();
                interimEl = null;
            }
        }

        // ── Toggle Mic (for manual click) ─────────────────────
        function toggleVoice() {
            if (!recognition) {
                recognition = createRecognition();
            }
            if (!recognition) {
                addSpeechTerminal('J.A.R.V.I.S.', 'Speech recognition is not supported on this browser. Please type your query instead.');
                return;
            }
            if (isRecognizing) {
                stopRecognition();
                addLog('MIC', 'MANUAL STOP');
                setReactorState('idle');
                startVoiceBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" x2="12" y1="19" y2="22"/></svg> VOICE INPUT';
            } else {
                if (synth.speaking) synth.cancel();
                startRecognition();
                startVoiceBtn.innerHTML = '<span style="color:#ff5714">●</span> MIC ON';
            }
        }

        startVoiceBtn.addEventListener('click', toggleVoice);
        reactorCore.addEventListener('click', toggleVoice);

        // ── Gemini-Style Natural TTS ──────────────────────────
        let voicesLoaded = false;
        synth.onvoiceschanged = () => { voicesLoaded = true; };

        function jarvisSpeak(text) {
            if (!synth || !text) return;

            // Stop mic briefly while speaking (to avoid hearing own voice)
            wasRecognizing = isRecognizing;
            if (isRecognizing) {
                try { recognition.stop(); } catch (e) {}
                isRecognizing = false;
            }

            setReactorState('speaking');
            addLog('JARVIS', 'SPEAKING');
            isSpeaking = true;

            const utterance = new SpeechSynthesisUtterance(text);

            // Prefer natural-sounding voices
            const voices = synth.getVoices();
            let voice = null;
            // Try Google UK English Female (natural), then Microsoft, then any English
            const preferred = ['google uk english female', 'google us english', 'microsoft zira', 'microsoft david', 'samantha'];
            for (const name of preferred) {
                voice = voices.find(v => v.name.toLowerCase().includes(name));
                if (voice) break;
            }
            if (!voice) voice = voices.find(v => v.lang.startsWith('en'));
            if (voice) utterance.voice = voice;

            // Natural human tone — not robotic
            utterance.pitch = 1.0;
            utterance.rate = 0.92;
            utterance.volume = 1.0;

            utterance.onend = () => {
                isSpeaking = false;
                setReactorState('idle');
                addLog('JARVIS', 'DONE');
                // Restart mic after speaking finishes
                if (!isRecognizing) {
                    setTimeout(() => startRecognition(), 200);
                }
            };

            utterance.onerror = () => {
                isSpeaking = false;
                setReactorState('idle');
                if (!isRecognizing) {
                    setTimeout(() => startRecognition(), 200);
                }
            };

            synth.speak(utterance);
        }
        let wasRecognizing = false;

        // ── Terminal Display ──────────────────────────────────
        function addSpeechTerminal(sender, text) {
            // Remove interim if showing
            showInterim('');

            const prompt = document.createElement('div');
            prompt.className = 'terminal-prompt';
            prompt.textContent = `${sender.toUpperCase()} >`;
            
            const txt = document.createElement('div');
            txt.className = 'terminal-text';
            txt.textContent = text;
            
            terminalOutput.appendChild(prompt);
            terminalOutput.appendChild(txt);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }

        // ── API Command ───────────────────────────────────────
        function sendCommand(cmdText) {
            if (!cmdText.trim()) return;
            if (cmdText.length < 2) return;
            
            // Track command time for follow-up window
            window._lastCommandTime = Date.now();

            addSpeechTerminal('USER', cmdText);
            addLog('API', 'POST COMMAND');
            setReactorState('processing');

            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: cmdText })
            })
            .then(res => res.json())
            .then(data => {
                setReactorState('idle');
                addSpeechTerminal('J.A.R.V.I.S.', data.message);
                addLog('API', 'RESPONSE RECEIVED');
                jarvisSpeak(data.spoken || data.message);
                updateStats();
            })
            .catch(err => {
                console.error(err);
                setReactorState('idle');
                addSpeechTerminal('J.A.R.V.I.S.', "Sir, my telemetry is reporting a connection exception.");
                addLog('API', 'ERROR');
            });
        }

        // ── Quick Commands ────────────────────────────────────
        function sendQuickCommand(cmd) {
            sendCommand(cmd);
        }

        // ── Text Input ────────────────────────────────────────
        function handleEnter(e) {
            if (e.key === 'Enter') {
                const text = userInput.value;
                userInput.value = '';
                sendCommand(text);
            }
        }

        // ── Telemetry / Gauges ────────────────────────────────
        function updateStats() {
            fetch('/api/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('cpu-percent').textContent = data.cpu_percent + '%';
                document.getElementById('cpu-bar').style.width = data.cpu_percent + '%';

                document.getElementById('mem-percent').textContent = data.mem_percent + '%';
                document.getElementById('mem-bar').style.width = data.mem_percent + '%';

                document.getElementById('disk-percent').textContent = data.disk_percent + '%';
                document.getElementById('disk-bar').style.width = data.disk_percent + '%';

                if (data.temp && data.temp !== 'N/A') {
                    document.getElementById('temp-val').textContent = data.temp + '°C';
                    let temp_pct = Math.min(100, Math.max(0, (data.temp - 30) * 1.6));
                    document.getElementById('temp-bar').style.width = temp_pct + '%';
                }

                if (data.battery && data.battery !== 'N/A') {
                    document.getElementById('battery-percent').textContent = data.battery + '%';
                    document.getElementById('battery-bar').style.width = data.battery + '%';
                }
            })
            .catch(err => console.debug("Error polling stats:", err));
        }

        // ── Init ──────────────────────────────────────────────
        setInterval(updateStats, 3500);
        updateStats();
        recognition = createRecognition();
        // Auto-start mic on page load (Gemini style — always ready)
        setTimeout(() => {
    startRecognition();
    // Check Ollama availability
fetch('/api/ollama/status').then(r=>r.json()).then(s=>{
    if(!s.available) {
        addLog('OLLAMA', 'NOT AVAILABLE — install for open-ended chat');
    } else {
        addLog('OLLAMA', `READY (${s.model})`);
    }
}).catch(()=>{});
addSpeechTerminal('J.A.R.V.I.S.', 'Say "Jarvis, cpu usage" or "Jarvis, what do you think about...?"');
}, 500);
console.log('J.A.R.V.I.S. HUD loaded — always listening for "jarvis"');
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    """Serve HUD page"""
    return render_template_string(HUD_HTML)

@app.route("/api/command", methods=["POST"])
def process_command():
    """REST API endpoint to process voice assistant commands"""
    data = request.json or {}
    command_text = data.get("command", "").strip() or data.get("text", "").strip()
    
    if not command_text:
        return jsonify({
            "message": "Missing command or text parameter.",
            "success": False
        }), 400
    
    try:
        # Call the voice assistant parser and core logic
        response_message = assistant.process_command(command_text)
        
        # Determine spoken summary (using the assistant's built-in formatting logic)
        # We can also check if the assistant has stored data
        last_data = getattr(assistant, "_last_response_data", None)
        
        return jsonify({
            "message": response_message,
            "spoken": response_message if len(response_message) < 200 else response_message[:150] + "...",
            "success": True,
            "data": last_data
        })
        
    except Exception as e:
        logger.error(f"Error processing command in Web UI: {e}")
        return jsonify({
            "message": f"Diagnostics failure: {str(e)}",
            "success": False
        }), 500

@app.route("/api/ollama/status", methods=["GET"])
def ollama_status():
    """Check if Ollama is available for open-ended conversation."""
    try:
        status = assistant.get_ollama_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"available": False, "error": str(e)})

@app.route("/api/ollama/install", methods=["GET"])
def ollama_install_guide():
    """Get instructions to install Ollama."""
    from voice_assistant.modules.ollama_chat import OllamaChat
    return jsonify({"instructions": OllamaChat.install_instructions()})

@app.route("/api/status", methods=["GET"])
def system_status():
    """Exposes real-time system metrics for HUD gauges"""
    import psutil
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        
        # Temperature
        temp = "N/A"
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for k, v in temps.items():
                    if v:
                        temp = int(v[0].current)
                        break
        except:
            pass
            
        # Battery
        battery = "N/A"
        try:
            bat = psutil.sensors_battery()
            if bat:
                battery = int(bat.percent)
        except:
            pass
            
        return jsonify({
            "cpu_percent": cpu,
            "mem_percent": mem,
            "disk_percent": disk,
            "temp": temp,
            "battery": battery,
            "state": assistant.get_status().get("state", "idle")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/voice", methods=["POST"])
def process_voice():
    """Server-side speech recognition endpoint.
    Accepts base64-encoded WAV audio from browser and runs Google STT.
    This is a fallback when browser Web Speech API fails.
    """
    data = request.json or {}
    audio_b64 = data.get("audio", "")
    
    if not audio_b64:
        return jsonify({"message": "No audio data", "success": False}), 400
    
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_b64)
        
        # Use speech_recognition library to process
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        # Write to temp file and read as AudioFile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        
        try:
            with sr.AudioFile(tmp_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            os.unlink(tmp_path)
            
            if text:
                response_message = assistant.process_command(text)
                return jsonify({
                    "message": response_message,
                    "spoken": response_message[:120] if len(response_message) > 120 else response_message,
                    "transcript": text,
                    "success": True
                })
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            logger.warning(f"Voice recognition failed: {e}")
            return jsonify({"message": f"Could not recognize speech", "success": False}), 400
            
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return jsonify({"message": str(e), "success": False}), 500

def run_server(port=5000):
    """Run server"""
    logger.info(f"Starting Iron Man J.A.R.V.I.S. HUD Web server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            pass
    run_server(port)
