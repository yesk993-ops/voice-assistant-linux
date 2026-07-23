# Linux Voice Assistant

A comprehensive voice assistant for controlling and managing your Linux system using natural language commands.

## Features

### 🔋 Power Management
- Shutdown, reboot, suspend, hibernate
- Lock screen, logout
- Scheduled shutdown with cancellation

### 🚀 Application Launcher
- Launch browsers (Firefox, Chrome, Brave, etc.)
- Open terminals (GNOME Terminal, Konsole, Alacritty, etc.)
- File managers (Nautilus, Dolphin, Thunar, etc.)
- Text editors (Gedit, VS Code, Vim, etc.)
- Any installed application by name

### 📁 File Management
- Create, delete, copy, move, rename files and directories
- List directory contents with details
- Search files by pattern
- Read file contents
- Disk usage analysis
- Find large files

### 🎛️ System Settings
- **Brightness**: Set, increase, decrease (0-100%)
- **Volume**: Set, increase, decrease, mute/unmute (0-100%)
- **Resolution**: Set screen resolution, list available modes
- Multi-monitor configuration

### ⚙️ System Commands
- System updates (apt, pacman, dnf, zypper)
- Run arbitrary shell commands
- Show uptime and logged-in users
- Systemd service management
- Package installation/removal/search

### 📊 System Monitoring
- CPU usage (overall and per-core)
- Memory and swap usage
- Disk usage and I/O statistics
- Temperature sensors and fan speeds
- Battery status
- Network interfaces and speed
- Top processes by CPU/memory
- Complete system summary

### ❓ Help & Support
- Contextual help for any command
- Interactive tutorial
- Troubleshooting guides
- Searchable help topics

## Installation

### Quick Start

```bash
# Clone or navigate to the project
cd voice_assistant

# Run setup script (installs dependencies)
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run the assistant
python main.py
```

### Manual Installation

1. **System Dependencies** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv \
    portaudio19-dev libasound2-dev libpulse-dev \
    espeak alsa-utils pulseaudio pavucontrol \
    xrandr brightnessctl
```

2. **Python Environment**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Optional Offline Speech Recognition**:
```bash
# Vosk (lightweight, fast)
pip install vosk
# Download model from https://alphacephei.com/vosk/models

# Whisper (high accuracy)
pip install openai-whisper

# Porcupine (wake word detection)
pip install pvporcupine
```

## Usage

### Running the Assistant

```bash
# Continuous listening mode (default)
python main.py

# Single command mode
python main.py --once

# Run module tests
python main.py --test

# Custom config file
python main.py --config /path/to/config.env
```

### Voice Commands Examples

**Power Management:**
- "Shutdown" / "Power off"
- "Reboot" / "Restart"
- "Suspend" / "Sleep"
- "Lock screen"
- "Shutdown in 10 minutes"
- "Cancel shutdown"

**Applications:**
- "Open browser" / "Open Firefox"
- "Open terminal"
- "Open file manager"
- "Open VS Code" / "Open code editor"
- "Open [app name]"
- "Close Firefox"

**File Operations:**
- "Create file notes.txt with content Hello World"
- "Create folder projects"
- "Delete file temp.txt"
- "Copy file.txt to backup.txt"
- "Move downloads/photo.jpg to pictures/"
- "Rename oldname.txt to newname.txt"
- "List files in downloads"
- "Find PDF files"
- "Read file notes.txt"

**System Settings:**
- "Set brightness to 70"
- "Increase brightness" / "Decrease brightness"
- "Set volume to 50"
- "Turn up the volume" / "Turn down the volume"
- "Mute" / "Unmute"
- "Set resolution to 1920x1080"
- "List resolutions"

**System Commands:**
- "Update system"
- "Run command ls -la"
- "Uptime"
- "Who is logged in"
- "Failed services"

**Monitoring:**
- "CPU usage"
- "Memory usage" / "RAM usage"
- "Disk usage"
- "Temperature"
- "Battery"
- "Network info"
- "Top processes"
- "System summary"

**Help:**
- "Help"
- "Help shutdown"
- "Tutorial"
- "List commands"

## Configuration

Edit `config/config.env` to customize:

```bash
# Speech Recognition
SPEECH_RECOGNITION_ENGINE=google  # google, vosk, whisper, sphinx
SPEECH_LANGUAGE=en-US
SPEECH_TIMEOUT=5

# Text-to-Speech
TTS_ENGINE=pyttsx3  # pyttsx3, gtts, espeak, festival
TTS_RATE=180
TTS_VOLUME=1.0

# Wake Word
WAKE_WORD=assistant
USE_WAKE_WORD=false

# Applications (customize for your system)
BROWSER_COMMAND=firefox
TERMINAL_COMMAND=gnome-terminal
FILE_MANAGER_COMMAND=nautilus
TEXT_EDITOR_COMMAND=gedit
CODE_EDITOR_COMMAND=code

# Hardware
BRIGHTNESS_DEVICE=intel_backlight  # Check /sys/class/backlight/
ALSA_CARD=default
ALSA_CONTROL=Master
```

### Desktop Environment Detection

The assistant auto-detects your desktop environment (GNOME, KDE, XFCE, etc.) and adjusts commands for:
- Screen locking
- Logout
- Settings

### Offline Speech Recognition (Vosk)

1. Install: `pip install vosk`
2. Download model from https://alphacephei.com/vosk/models
3. Extract and set `VOSK_MODEL_PATH` in config
4. Set `SPEECH_RECOGNITION_ENGINE=vosk`

### Wake Word Detection (Porcupine)

1. Get free access key from https://console.picovoice.ai/
2. Install: `pip install pvporcupine`
3. Set `PORCUPINE_ACCESS_KEY` in config
4. Set `USE_WAKE_WORD=true`

## Architecture

```
voice_assistant/
├── main.py                 # Entry point
├── config/
│   ├── config.env          # Configuration (create from example)
│   └── config.env.example  # Template
├── modules/
│   ├── __init__.py         # Package exports
│   ├── speech.py           # Speech recognition (Google, Vosk, Whisper)
│   ├── tts.py              # Text-to-speech (pyttsx3, gTTS, espeak)
│   ├── power.py            # Power management
│   ├── apps.py             # Application launcher
│   ├── files.py            # File system operations
│   ├── system_settings.py  # Brightness, volume, resolution
│   ├── system_commands.py  # Updates, commands, systemd
│   ├── system_monitor.py   # CPU, memory, disk, sensors
│   ├── help.py             # Help system & tutorials
│   └── command_parser.py   # Natural language parsing
├── requirements.txt        # Python dependencies
└── setup.sh               # Automated installation script
```

## Supported Distributions

- Ubuntu / Debian / Mint / Pop!_OS
- Arch / Manjaro / EndeavourOS
- Fedora / RHEL / CentOS
- openSUSE
- Any systemd-based Linux

## Troubleshooting

### Microphone not working
```bash
# List devices
arecord -l

# Test recording
arecord -d 5 test.wav && aplay test.wav

# Adjust sensitivity in config
SPEECH_ENERGY_THRESHOLD=4000
```

### No audio output
```bash
# Test speakers
speaker-test -t wav -c 2

# Check PulseAudio
pulseaudio --check || pulseaudio --start

# Install pavucontrol for GUI mixer
sudo apt install pavucontrol
```

### Brightness control not working
```bash
# Find backlight device
ls /sys/class/backlight/

# Set in config
BRIGHTNESS_DEVICE=intel_backlight  # or amdgpu_bl0, nvidia_0, etc.

# Add kernel parameter if needed
# GRUB_CMDLINE_LINUX_DEFAULT="acpi_backlight=vendor"
```

### Permission errors (shutdown, updates)
Configure passwordless sudo for specific commands:
```bash
# Edit sudoers
sudo visudo

# Add (replace username):
username ALL=(ALL) NOPASSWD: /usr/bin/systemctl poweroff, /usr/bin/systemctl reboot, /usr/bin/apt update, /usr/bin/apt upgrade
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## License

MIT License - Feel free to use and modify for personal or commercial projects.

## Acknowledgments

- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Speech recognition library
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Offline TTS
- [psutil](https://github.com/giampaolo/psutil) - System monitoring
- [screen-brightness-control](https://github.com/SinClair/screen-brightness-control) - Brightness control
- [Vosk](https://alphacephei.com/vosk/) - Offline speech recognition
- [Porcupine](https://picovoice.ai/platform/porcupine/) - Wake word detection