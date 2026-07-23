#!/bin/bash
# Voice Assistant Setup Script
# Installs dependencies and configures the voice assistant

set -e

echo "========================================"
echo "Linux Voice Assistant Setup"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Please don't run this script as root${NC}"
   exit 1
fi

# Detect distribution


DISTRO=$(. /etc/os-release; echo "$ID")
echo -e "${YELLOW}Detected distribution: $DISTRO${NC}"

# Install system dependencies
install_system_deps() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    
    case $DISTRO in
        ubuntu|debian|linuxmint|mint|pop)
            sudo apt update
            sudo apt install -y \
                python3 python3-pip python3-venv \
                python3-pyaudio \
                portaudio19-dev \
                libasound2-dev \
                libpulse-dev \
                libespeak1 \
                espeak \
                alsa-utils \
                pulseaudio \
                pavucontrol \
                xrandr \
                brightnessctl \
                || echo -e "${RED}Some packages failed to install${NC}"
            ;;
        arch|manjaro|endeavour)
            sudo pacman -S --needed \
                python python-pip \
                portaudio \
                alsa-lib \
                pulseaudio \
                pulseaudio-alsa \
                espeak \
                xorg-xrandr \
                brightnessctl \
                || echo -e "${RED}Some packages failed to install${NC}"
            ;;
        fedora|rhel|centos)
            sudo dnf install -y \
                python3 python3-pip \
                portaudio-devel \
                alsa-lib-devel \
                pulseaudio-libs-devel \
                espeak \
                xrandr \
                brightnessctl \
                || echo -e "${RED}Some packages failed to install${NC}"
            ;;
        opensuse*)
            sudo zypper install -y \
                python3 python3-pip \
                portaudio-devel \
                alsa-devel \
                pulseaudio-devel \
                espeak \
                xrandr \
                brightnessctl \
                || echo -e "${RED}Some packages failed to install${NC}"
            ;;
        *)
            echo -e "${YELLOW}Unknown distribution. Please install dependencies manually:${NC}"
            echo "  - python3, pip, portaudio, alsa, pulseaudio, espeak, xrandr, brightnessctl"
            ;;
    esac
}

# Create virtual environment
create_venv() {
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd "$(dirname "$0")"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
}

# Install Python dependencies
install_python_deps() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    source venv/bin/activate
    
    # Core dependencies
    pip install -r requirements.txt
    
    # Optional: Offline speech recognition (Vosk)
    echo -e "${YELLOW}Installing optional offline speech recognition...${NC}"
    pip install vosk || echo "Vosk installation failed (optional)"
    
    # Optional: Whisper for high-quality offline recognition
    pip install openai-whisper || echo "Whisper installation failed (optional)"
    
    # Optional: Porcupine for wake word detection
    pip install pvporcupine || echo "Porcupine installation failed (optional)"
}

# Configure audio
configure_audio() {
    echo -e "${YELLOW}Configuring audio...${NC}"
    
    # Add user to audio group
    sudo usermod -a -G audio $USER
    
    # Test audio
    echo "Testing audio playback..."
    speaker-test -t wav -c 2 -l 1 2>/dev/null || echo "Audio test failed (may need manual config)"
}

# Create config file
create_config() {
    echo -e "${YELLOW}Creating configuration...${NC}"
    cd "$(dirname "$0")"
    
    if [ ! -f config/config.env ]; then
        cat > config/config.env << 'EOF'
# Voice Assistant Configuration
# Customize these settings for your system

# Speech Recognition Settings
SPEECH_RECOGNITION_ENGINE=google
SPEECH_LANGUAGE=en-US
SPEECH_TIMEOUT=5
SPEECH_PHRASE_TIME_LIMIT=10
SPEECH_ENERGY_THRESHOLD=300

# Text-to-Speech Settings
TTS_ENGINE=pyttsx3
TTS_RATE=180
TTS_VOLUME=1.0
TTS_VOICE=

# Wake Word Settings
WAKE_WORD=assistant
USE_WAKE_WORD=false

# System Settings
LOG_LEVEL=INFO
LOG_FILE=voice_assistant.log

# Application Paths (customize for your system)
BROWSER_COMMAND=firefox
TERMINAL_COMMAND=gnome-terminal
FILE_MANAGER_COMMAND=nautilus
TEXT_EDITOR_COMMAND=gedit
CODE_EDITOR_COMMAND=code

# System Commands
SHUTDOWN_COMMAND=systemctl poweroff
REBOOT_COMMAND=systemctl reboot
SUSPEND_COMMAND=systemctl suspend
HIBERNATE_COMMAND=systemctl hibernate
LOCK_COMMAND=gnome-screensaver-command -l
LOGOUT_COMMAND=gnome-session-quit --no-prompt

# Update Commands (adjust for your distro)
UPDATE_COMMAND=sudo apt update && sudo apt upgrade -y

# Audio Settings (for ALSA)
ALSA_CARD=default
ALSA_CONTROL=Master

# Screen Brightness
BRIGHTNESS_DEVICE=intel_backlight

# Network Interface for monitoring
NETWORK_INTERFACE=auto
EOF
        echo -e "${GREEN}Created config/config.env${NC}"
    else
        echo -e "${YELLOW}Config file already exists${NC}"
    fi
}

# Download Vosk model (optional)
download_vosk_model() {
    echo -e "${YELLOW}Downloading Vosk model (optional)...${NC}"
    MODEL_DIR="$HOME/.vosk-model"
    
    if [ ! -d "$MODEL_DIR" ]; then
        mkdir -p "$MODEL_DIR"
        cd "$MODEL_DIR"
        # Small English model (~50MB)
        wget -q https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip 2>/dev/null || \
            echo "Could not download Vosk model automatically"
        if [ -f vosk-model-small-en-us-0.15.zip ]; then
            unzip -q vosk-model-small-en-us-0.15.zip
            mv vosk-model-small-en-us-0.15/* .
            rm -rf vosk-model-small-en-us-0.15.zip
            echo -e "${GREEN}Vosk model downloaded to $MODEL_DIR${NC}"
        fi
    else
        echo -e "${YELLOW}Vosk model already exists${NC}"
    fi
}

# Test installation
test_installation() {
    echo -e "${YELLOW}Testing installation...${NC}"
    source venv/bin/activate
    cd "$(dirname "$0")"
    python main.py --test
}

# Main setup flow
main() {
    echo -e "${GREEN}Starting setup...${NC}"
    
    install_system_deps
    create_venv
    install_python_deps
    configure_audio
    create_config
    
    # Optional components
    read -p "Download Vosk offline speech model? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        download_vosk_model
    fi
    
    test_installation
    
    echo -e "${GREEN}========================================"
    echo "Setup complete!"
    echo "========================================"
    echo ""
    echo "To run the voice assistant:"
    echo "  cd $(dirname "$0")"
    echo "  source venv/bin/activate"
    echo "  python main.py"
    echo ""
    echo "For single command mode:"
    echo "  python main.py --once"
    echo ""
    echo "Configuration file: config/config.env"
    echo "Edit it to customize your settings."
    echo ""
    echo -e "${YELLOW}Note: You may need to log out and back in for audio group changes to take effect.${NC}"
}

main