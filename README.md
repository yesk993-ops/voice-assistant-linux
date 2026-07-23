# 🛸 J.A.R.V.I.S. Voice Assistant — Gemini-Style Hands-Free HUD
> **The Ultimate Iron Man-Style System Assistant for Linux & Windows**

Welcome to **J.A.R.V.I.S.** (Just A Rather Very Intelligent System), a production-grade, natural-language voice assistant that gives you complete command over your computer. It features an incredibly sleek, **Iron Man style holographic HUD Web UI** with real-time hardware telemetry and interactive audio visualizers!

---

## 🚀 The Global Quick-Start Commands (Zero-Hassle Installation)

This assistant includes a **smart cross-platform installer** that automatically detects your Operating System and Linux flavor (Ubuntu, Debian, RHEL, Fedora, CentOS, Arch, OpenSUSE, or Windows), installs all required system libraries, sets up a clean virtual environment, installs packages, and boots up the J.A.R.V.I.S. Core Web Interface instantly!

### 🐧 For All Linux Flavors (Ubuntu, RHEL, Arch, Fedora, openSUSE, etc.)
Open your terminal and run this single-line command:
```bash
curl -sSL "https://raw.githubusercontent.com/yesk993-ops/voice-assistant-linux/main/installer.py" | python3
```

### 🎯 After installation — Systemd Service (run once):
```bash
systemctl --user start jarvis    # Start J.A.R.V.I.S. as a background service
systemctl --user enable jarvis   # Auto-start on login
```
Then open **http://localhost:5000** — say **"Jarvis, what's the CPU usage?"**

## 🎯 How Voice Mode Works (Hands-Free, Like Gemini)

| Feature | How it works |
|---------|-------------|
| **Wake word** | Say **"Jarvis"** followed by your command — e.g. *"Jarvis, what's the CPU?"* |
| **Follow-up window** | After J.A.R.V.I.S. responds, you have **10 seconds** to ask a follow-up without saying "Jarvis" |
| **Always-on mic** | Mic activates automatically on page load — no buttons to press |
| **Interrupt** | Speak while J.A.R.V.I.S. is talking and it stops to listen |
| **Natural voice** | Uses Google/Microsoft voices with natural pitch and rate |
| **Fallback** | If Web Speech fails, audio can be sent to the server for recognition via `/api/voice` |
*Note: The installer automatically handles standard dependency installation, using `sudo` on your system package manager (`apt`, `dnf`, `pacman`, or `zypper`) as necessary.*

### 🪟 For Windows
Open your PowerShell terminal and run:
```powershell
curl -o installer.py "https://raw.githubusercontent.com/yesk993-ops/voice-assistant-linux/main/installer.py"; python installer.py
```

---

## 🎨 The Iron Man Mark-85 HUD Interface
Once the installer finishes running, J.A.R.V.I.S. will start serving on:
👉 **`http://localhost:5000`**

### What’s inside the Holographic HUD:
1. **Dynamic Glowing Arc Reactor**: A multi-ring centered visualizer that rotates and pulses, shifting states as J.A.R.V.I.S. responds:
   - 🔵 **Blue**: Idle / Ready
   - 🟠 **Orange**: Listening (capturing your voice)
   - ⚪ **White**: Decrypting / Processing Intent
   - 🟢 **Green**: Speaking / Transcribing
2. **Real-Time Telemetry Panels**: Glowing futuristic gauges rendering live system health:
   - **CPU load & core utilities**
   - **RAM / Memory allocation**
   - **Primary disk storage capacity**
   - **Core hardware temperature**
   - **Battery power supply**
3. **In-Browser Web Speech STT & TTS**: Zero local microphone configuration or drivers needed! Just click the centered glowing **Arc Reactor Core** to talk directly to J.A.R.V.I.S., and he will speak back using an optimized, pitch-shifted robotic English voice.
4. **Diagnostics Log & Interactive Command Center**: View API request logs in real-time or click-to-run quick diagnosis instructions.

---

## 🛠️ Core Command Capabilities

You can control your system by typing in the input bar or speaking into your microphone:

* **📊 Monitoring**: *"CPU usage"*, *"Memory load"*, *"Disk utilization"*, *"Core temperature"*, *"Battery"*, or *"System summary"*.
* **🔋 Power Management**: *"Shutdown"*, *"Reboot"*, *"Lock screen"*, *"Sleep"* (Suspend), or *"Shutdown in 15 minutes"*.
* **📂 File Management**: 
  - *"Create folder Projects"*, *"Create file notes.txt with content Hello World"*
  - *"List current directory"*, *"List files in Downloads"*
  - *"Read file notes.txt"*, *"Get file info of image.png"*
  - *"Copy file.txt to backup.txt"*, *"Delete folder Temp force"*
* **🚀 Application Launcher**: *"Open terminal"*, *"Open Firefox"*, *"Open VS Code"*, *"Close Spotify"*, or *"Launch [app_name]"*.
* **🎛️ System Settings**: *"Set volume to 60%"*, *"Mute"*, *"Unmute"*, *"Set brightness to 80%"*, *"List resolutions"*, or *"Set resolution 1920x1080"*.
* **⚙️ System Commands**: *"Update system"* (automatically runs apt/dnf/pacman upgrade), *"Run command ls -lh"*, *"Show uptime"*, or *"Who is logged in"*.

---

## 📦 How to Manual Install (If not using the global script)

If you prefer to clone the repository and run things manually, follow these instructions:

### 1. Pre-requisites (System packages)
* **Debian/Ubuntu**:
  ```bash
  sudo apt install -y python3-dev python3-venv portaudio19-dev libasound2-dev libpulse-dev espeak alsa-utils pulseaudio brightnessctl x11-xserver-utils
  ```
* **RHEL/Fedora/CentOS**:
  ```bash
  sudo dnf install -y epel-release
  sudo dnf install -y python3-devel gcc gcc-c++ make portaudio-devel alsa-lib-devel pulseaudio-libs-devel espeak brightnessctl xrandr
  ```
* **Arch Linux**:
  ```bash
  sudo pacman -S --needed --noconfirm base-devel python portaudio alsa-lib pulseaudio espeak-ng brightnessctl xorg-xrandr
  ```

### 2. Setting Up Python environment
```bash
# Clone the repository
git clone https://github.com/yesk993-ops/voice-assistant-linux.git
cd voice-assistant-linux

# Establish virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install libraries
pip install --upgrade pip
pip install -r voice_assistant/requirements.txt
pip install flask
```

### 3. Execution Modes
* **Start Web HUD Server**:
  ```bash
  python3 voice_assistant/web_server.py
  ```
* **Start Terminal CLI (Continuous listening loop)**:
  ```bash
  python3 voice_assistant/main.py
  ```
* **Run Single CLI Command**:
  ```bash
  python3 voice_assistant/main.py --once
  ```
* **Run Diagnostic Test Suite**:
  ```bash
  python3 voice_assistant/main.py --test
  ```

---

## 🏛️ Project Architecture
```
voice_assistant/
├── main.py                 # Core Assistant entrypoint and command registry
├── web_server.py           # Flask HUD backend and J.A.R.V.I.S single page UI
├── config/
│   └── config.env          # System & application paths settings
└── modules/
    ├── speech.py           # Speech Recognition (Google, Vosk, Whisper) with Stdin fallback
    ├── tts.py              # Text-To-Speech (pyttsx3, gTTS, espeak)
    ├── power.py            # Shutdown, Reboot, Suspend, Lock Screen (DE-aware)
    ├── apps.py             # Desktop application execution & fuzzy mapping
    ├── files.py            # CRUD operations & Disk metrics
    ├── system_settings.py  # ALSA volume, PulseAudio devices, brightnessctl, xrandr
    ├── system_monitor.py   # Psutil memory/CPU metrics & hardware sensors
    ├── help.py             # Searchable help topic index & tutorials
    ├── command_parser.py   # Natural Language Regex Parsing & Entity Extraction
    └── response_formatter.py # Structuring response types (STATUS, DESTRUCTIVE, etc.)
```

---

## 🛡️ License
Distributed under the MIT License. Feel free to customize and expand J.A.R.V.I.S. for your own smart-home or hardware setups!
