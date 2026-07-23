"""
J.A.R.V.I.S. Unified Cross-Platform Installer & Bootstrapper
Supported OS: All Linux Flavors (Debian, Ubuntu, RHEL, CentOS, Fedora, Arch, OpenSUSE) & Windows
Features: Detects OS, installs system and python dependencies, starts Web HUD server.
"""

import os
import sys
import platform
import subprocess
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='[INSTALLER] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, shell=False, sudo=False):
    """Run a system command and return success"""
    if sudo and platform.system() != "Windows" and os.getuid() != 0:
        if isinstance(cmd, list):
            cmd = ["sudo"] + cmd
        else:
            cmd = f"sudo {cmd}"
            
    logger.info(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=shell, check=True)
        return True
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return False

def get_linux_distro():
    """Identify the Linux distribution family"""
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
            if "ubuntu" in content or "debian" in content or "mint" in content or "pop" in content:
                return "debian"
            elif "fedora" in content or "rhel" in content or "centos" in content:
                return "rhel"
            elif "arch" in content or "manjaro" in content or "endeavour" in content:
                return "arch"
            elif "suse" in content:
                return "suse"
    except Exception as e:
        logger.warning(f"Could not read /etc/os-release: {e}")
    return "unknown"

def install_linux_dependencies(distro):
    """Install audio, compilers and settings packages based on distro family"""
    logger.info(f"Installing system packages for Linux flavor: {distro.upper()}")
    
    if distro == "debian":
        logger.info("Updating apt package lists...")
        run_command(["apt-get", "update"], sudo=True)
        # Install build essentials, portaudio dev headers, and tools
        pkgs = [
            "python3-dev", "python3-pip", "python3-venv",
            "build-essential", "portaudio19-dev", "libasound2-dev", "libpulse-dev",
            "libespeak1", "espeak", "alsa-utils", "pulseaudio", "brightnessctl", "xrandr"
        ]
        return run_command(["apt-get", "install", "-y"] + pkgs, sudo=True)
        
    elif distro == "rhel":
        # Group install development tools and headers
        logger.info("Installing development tools and EPEL if needed...")
        run_command(["dnf", "install", "-y", "epel-release"], sudo=True)
        pkgs = [
            "python3-devel", "gcc", "gcc-c++", "make",
            "portaudio-devel", "alsa-lib-devel", "pulseaudio-libs-devel",
            "espeak", "brightnessctl", "xrandr"
        ]
        return run_command(["dnf", "install", "-y"] + pkgs, sudo=True)
        
    elif distro == "arch":
        pkgs = [
            "base-devel", "python", "python-pip",
            "portaudio", "alsa-lib", "pulseaudio", "espeak-ng",
            "brightnessctl", "xorg-xrandr"
        ]
        return run_command(["pacman", "-S", "--needed", "--noconfirm"] + pkgs, sudo=True)
        
    elif distro == "suse":
        pkgs = [
            "devel_basis", "python3-devel",
            "portaudio-devel", "alsa-devel", "pulseaudio-devel",
            "espeak", "brightnessctl", "xrandr"
        ]
        return run_command(["zypper", "install", "-y"] + pkgs, sudo=True)
        
    else:
        logger.warning("Unknown Linux distribution. Please ensure portaudio, espeak, pulseaudio are installed manually.")
        return True

def setup_config_file():
    """Ensure a default config.env exists"""
    config_dir = Path("config") if "Path" in globals() else None
    if not config_dir:
        from pathlib import Path
        config_dir = Path("config")
        
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.env"
    
    if not config_file.exists():
        logger.info("Generating default configuration file at config/config.env...")
        config_content = """# J.A.R.V.I.S. System Configuration
SPEECH_RECOGNITION_ENGINE=google
SPEECH_LANGUAGE=en-US
SPEECH_TIMEOUT=5
TTS_ENGINE=pyttsx3
TTS_RATE=180
TTS_VOLUME=1.0
WAKE_WORD=assistant
USE_WAKE_WORD=false
LOG_LEVEL=INFO
LOG_FILE=voice_assistant.log
BROWSER_COMMAND=firefox
TERMINAL_COMMAND=gnome-terminal
FILE_MANAGER_COMMAND=nautilus
TEXT_EDITOR_COMMAND=gedit
CODE_EDITOR_COMMAND=code
SHUTDOWN_COMMAND=systemctl poweroff
REBOOT_COMMAND=systemctl reboot
SUSPEND_COMMAND=systemctl suspend
HIBERNATE_COMMAND=systemctl hibernate
LOCK_COMMAND=gnome-screensaver-command -l
UPDATE_COMMAND=sudo apt update && sudo apt upgrade -y
"""
        config_file.write_text(config_content)
        logger.info("Configuration file written successfully.")

def main():
    logger.info("=== J.A.R.V.I.S. SYSTEM CORE CONVERGENCE ===")
    os_name = platform.system()
    logger.info(f"Target System Operating System detected: {os_name.upper()}")
    
    # Step 1: Install System dependencies
    if os_name == "Linux":
        distro = get_linux_distro()
        success = install_linux_dependencies(distro)
        if not success:
            logger.warning("Some system package installations might have failed. Continuing...")
    elif os_name == "Windows":
        logger.info("Windows detected. System packages are pre-compiled in python wheels.")
    elif os_name == "Darwin":
        logger.info("macOS detected. Installing portaudio via brew...")
        if shutil.which("brew"):
            run_command(["brew", "install", "portaudio", "espeak"])
        else:
            logger.warning("Homebrew not found. Please install portaudio manually.")
            
    # Step 2: Establish Virtual Environment
    venv_dir = "venv"
    if not os.path.exists(venv_dir):
        logger.info("Creating a clean Python virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        
    # Get venv python/pip executables
    if os_name == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")
        
    # Step 3: Upgrade pip & install requirements
    logger.info("Upgrading pip inside the virtual environment...")
    subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
    
    logger.info("Installing core Python packages inside venv...")
    # Read requirements
    reqs_path = "voice_assistant/requirements.txt"
    if os.path.exists(reqs_path):
        subprocess.run([pip_path, "install", "-r", reqs_path], check=True)
    else:
        logger.warning(f"Could not find requirements at {reqs_path}")
        
    # Ensure Flask is installed
    logger.info("Installing Flask web server...")
    subprocess.run([pip_path, "install", "flask"], check=True)
    
    # Step 4: Write default configuration
    setup_config_file()
    
    # Step 5: Boot J.A.R.V.I.S.!
    logger.info("Setup complete! Initializing J.A.R.V.I.S. Core Web HUD...")
    server_path = "voice_assistant/web_server.py"
    
    try:
        # Start server and let it run
        subprocess.run([python_path, server_path])
    except KeyboardInterrupt:
        logger.info("J.A.R.V.I.S. server shut down by user request.")

if __name__ == "__main__":
    main()
