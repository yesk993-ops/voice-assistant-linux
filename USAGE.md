# 🚀 J.A.R.V.I.S. — Complete Usage Guide

> **Hands-free voice assistant for Linux | Like Google Gemini on your desktop**

---

## 📦 Step 1: Install (One-Time)

Open your terminal and paste this single command:

```bash
curl -sSL "https://raw.githubusercontent.com/yesk993-ops/voice-assistant-linux/main/installer.py" | python3
```

**What happens:**
1. 🔍 Detects your Linux distro (Ubuntu, Debian, Fedora, Arch, etc.)
2. 📥 Installs system packages (`python3`, `portaudio`, `espeak`, etc.)
3. 🐍 Creates a Python virtual environment (`venv/`)
4. 📦 Installs all Python dependencies
5. ⚙️ Generates configuration at `config/config.env`
6. 🎯 Sets up the **systemd service** for background running
7. 🌐 Opens the Web HUD at `http://localhost:5000`

The installer will print instructions like this at the end:

```
=== J.A.R.V.I.S. SYSTEMD SERVICE ===
INSTALLED! Manage with:
  systemctl --user start jarvis      # Start server
  systemctl --user stop jarvis       # Stop server
  systemctl --user restart jarvis    # Restart after pull
  systemctl --user enable jarvis     # Auto-start on login
  journalctl --user -u jarvis -f     # View live logs
==================================
```

---

## ⚙️ Step 2: Start the Service (Background Mode)

After installation, **close the browser tab** (the one that auto-opened) and run:

```bash
# Start J.A.R.V.I.S. as a background service
systemctl --user start jarvis

# (Optional) Auto-start on every login
systemctl --user enable jarvis
```

**Check if it's running:**
```bash
systemctl --user status jarvis
```
You should see: `Active: active (running)`

---

## 🌐 Step 3: Open the HUD Interface

Open your browser and go to:

```
http://localhost:5000
```

You'll see the **Iron Man J.A.R.V.I.S. Holographic HUD** with:
- 🌀 Glowing Arc Reactor animation
- 📊 Live CPU / Memory / Disk / Temperature / Battery gauges
- 💬 Text input at the bottom
- 📋 Command suggestion buttons on the right
- 📝 Diagnostics log panel

---

## 🎤 Step 4: Start Talking (Hands-Free)

### ⚠️ First-time: Allow Microphone

When the page loads, your browser will ask: **"Allow microphone access?"**

| Browser | What to do |
|---------|-----------|
| **Chrome** | Click **Allow** in the popup (top-left of address bar) |
| **Edge** | Click **Allow** in the popup |
| **Firefox** | Click **Allow** when prompted |

If you accidentally clicked **Block**:
- Click the 🔒 lock icon in the address bar
- Find **Microphone** → Change from *Block* to *Allow*
- Reload the page

### 🗣️ How to Speak

**The mic is always on — no buttons to press!**

| You say | What happens |
|---------|-------------|
| *"Jarvis, what's the CPU usage?"* | 🖥️ Shows CPU stats + speaks back |
| *"Jarvis, how much battery is left?"* | 🔋 Battery percentage + time remaining |
| *"Jarvis, what's the memory at?"* | 💾 RAM usage |
| *"Jarvis, open Firefox"* | 🌐 Launches Firefox |
| *"Jarvis, set volume to 50"* | 🔊 Adjusts system volume |
| *"Jarvis, help"* | ❓ Lists all available commands |
| *"Jarvis, system summary"* | 📋 Full system overview |

### 💬 Follow-up Questions (Gemini-Style)

After J.A.R.V.I.S. responds, you have **10 seconds** to ask follow-ups **without** saying "Jarvis":

```
You:    "Jarvis, what's the CPU usage?"
Jarvis: "Your CPU is at 45% — doing fine."

You:    "and what about memory?"          ← No "Jarvis" needed!
Jarvis: "Memory at 67% — still comfortable."

You:    "how much disk space is left?"    ← Also works!
Jarvis: "Storage at / is 69% used — still okay."
```

### 🔇 Interrupting

J.A.R.V.I.S. speaks back to you. If you want to interrupt and ask something else:

```
Jarvis: "Your CPU is at 45% running at 2500..."
You:    "Jarvis, open terminal"           ← Speak over it!
Jarvis: [Stops talking, opens terminal]
```

### ⌨️ Typing Instead

If you prefer not to use voice:
1. Type your command in the text input at the bottom
2. Press **Enter**
3. J.A.R.V.I.S. responds both in text and speech

---

## 🔄 Service Management Commands

| Command | What it does |
|---------|-------------|
| `systemctl --user start jarvis` | ▶️ **Start** the J.A.R.V.I.S. web server |
| `systemctl --user stop jarvis` | ⏹️ **Stop** the J.A.R.V.I.S. web server |
| `systemctl --user restart jarvis` | 🔄 **Restart** (useful after pulling updates) |
| `systemctl --user status jarvis` | 📊 **Check** if it's running |
| `systemctl --user enable jarvis` | 🔁 **Auto-start** on every login |
| `systemctl --user disable jarvis` | 🛑 **Remove** auto-start |
| `journalctl --user -u jarvis -f` | 📝 **View live logs** (press `Ctrl+C` to exit) |

### If the service wasn't installed (manual install):

If you see `Unit jarvis.service could not be found.`, run this once:

```bash
cd ~/voice-assistant-linux && bash install-service.sh
```

Then try `systemctl --user start jarvis` again.

### Quick start/stop flow:

```bash
# Start it
systemctl --user start jarvis

# Open http://localhost:5000 in your browser and talk to it
# ...

# Stop it when done
systemctl --user stop jarvis
```

### After pulling new updates:

```bash
cd ~/voice-assistant-linux
git pull

# Restart to apply changes
systemctl --user restart jarvis
```

---

## 📝 Config File

Located at `~/voice-assistant-linux/config/config.env`:

```env
SPEECH_RECOGNITION_ENGINE=google    # google, vosk, whisper, sphinx
SPEECH_LANGUAGE=en-US               # Your language
SPEECH_TIMEOUT=5                    # Seconds to wait for speech
TTS_ENGINE=pyttsx3                  # Text-to-speech engine
TTS_RATE=180                        # Speech speed
WAKE_WORD=assistant                 # Wake word (for CLI mode not web)
USE_WAKE_WORD=false                  # Wake word on/off (CLI mode)
LOG_LEVEL=INFO                      # INFO, DEBUG, WARNING
```

Edit with `nano ~/voice-assistant-linux/config/config.env`, then restart:
```bash
systemctl --user restart jarvis
```

---

## ❌ Troubleshooting

### "MIC: ERROR: not-allowed" or "MIC: BLOCKED"
→ Go to browser settings → Privacy → Microphone → **Allow** for `localhost`

### "MIC: ERROR: network"
→ Web Speech API can't reach Google's servers. Switch to **typing** (input box + Enter).

### Service won't start
```bash
journalctl --user -u jarvis -e --no-pager
```
This shows the last error logs.

### Nothing happens when I speak
→ Make sure you're saying **"Jarvis"** first (case insensitive)

### Port 5000 already in use
→ Kill the old process: `systemctl --user stop jarvis` then start again

### How do I update?
```bash
cd ~/voice-assistant-linux && git pull && systemctl --user restart jarvis
```

---

## 📁 Project Structure

```
~/voice-assistant-linux/
├── installer.py              # Global install script
├── config/config.env         # Your settings
├── voice_assistant/
│   ├── web_server.py         # Flask web server + HUD HTML/CSS/JS
│   ├── main.py               # Core assistant logic
│   ├── jarvis.service        # Systemd service template
│   └── modules/
│       ├── speech.py         # Speech recognition
│       ├── tts.py            # Text-to-speech
│       ├── power.py          # Shutdown/reboot/suspend
│       ├── apps.py           # Application launcher
│       ├── files.py          # File management
│       ├── system_settings.py # Volume/brightness/resolution
│       ├── system_monitor.py # CPU/memory/disk/battery/temp
│       ├── system_commands.py # Uptime/users/updates
│       ├── command_parser.py # Natural language parser
│       ├── response_formatter.py # Conversational responses
│       └── help.py           # Help system
└── venv/                     # Python virtual environment
```
