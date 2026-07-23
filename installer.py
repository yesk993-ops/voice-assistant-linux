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

REPO_URL = "https://github.com/yesk993-ops/voice-assistant-linux.git"


def get_project_root():
    """
    Determine the project root directory.
    If the required project files (voice_assistant/web_server.py) don't exist
    locally, clone the repository automatically. This handles both local
    checkouts and curl | python3 execution.
    """
    # 1) Check if CWD is already inside a valid checkout
    candidate = os.getcwd()
    marker = os.path.join(candidate, "voice_assistant", "web_server.py")
    if os.path.isfile(marker):
        return candidate

    # 2) Check the directory where this script file lives (local execution)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        marker = os.path.join(script_dir, "voice_assistant", "web_server.py")
        if os.path.isfile(marker):
            return script_dir
    except Exception:
        pass

    # 3) Not inside a checkout — clone the repository
    target_dir = os.path.join(os.getcwd(), "voice-assistant-linux")
    if os.path.isdir(target_dir):
        logger.info(f"Found existing clone at {target_dir}")
    else:
        logger.info(f"Cloning repository into {target_dir}...")
        subprocess.run(["git", "clone", "--depth=1", REPO_URL, target_dir], check=True)
        logger.info("Repository cloned successfully.")
    return target_dir


INSTALLER_DIR = get_project_root()


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
        pkgs = [
            "python3-dev", "python3-pip", "python3-venv",
            "build-essential", "portaudio19-dev", "libasound2-dev", "libpulse-dev",
            "libespeak1", "espeak", "alsa-utils", "pulseaudio", "brightnessctl",
            "x11-xserver-utils"
        ]
        return run_command(["apt-get", "install", "-y"] + pkgs, sudo=True)

    elif distro == "rhel":
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
    from pathlib import Path
    config_dir = Path(INSTALLER_DIR) / "config"
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


def setup_systemd_service():
    """Install J.A.R.V.I.S. as a systemd user service for easy management"""
    service_path = os.path.join(INSTALLER_DIR, "voice_assistant", "jarvis.service")
    if not os.path.isfile(service_path):
        logger.warning("jarvis.service template not found, skipping systemd setup.")
        return

    # Read template and substitute INSTALL_DIR placeholder
    with open(service_path) as f:
        content = f.read()

    content = content.replace("__INSTALL_DIR__", INSTALLER_DIR)

    # Write to systemd user directory (~/.config/systemd/user/)
    systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(systemd_dir, exist_ok=True)

    target_service = os.path.join(systemd_dir, "jarvis.service")
    with open(target_service, "w") as f:
        f.write(content)

    logger.info(f"systemd user service installed at: {target_service}")

    # Reload systemd daemon
    subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    logger.info("systemd daemon reloaded.")

    print()
    logger.info("=== J.A.R.V.I.S. SYSTEMD SERVICE READY ===")
    logger.info("Manage J.A.R.V.I.S. with these commands:")
    logger.info(f"  systemctl --user start jarvis      # Start the web server")
    logger.info(f"  systemctl --user stop jarvis       # Stop the web server")
    logger.info(f"  systemctl --user restart jarvis    # Restart with latest changes")
    logger.info(f"  systemctl --user enable jarvis     # Auto-start on login")
    logger.info(f"  systemctl --user status jarvis     # Check status")
    logger.info(f"  journalctl --user -u jarvis -f     # View live logs")
    logger.info("===========================================")


def main():
    logger.info("============================================")
    logger.info("   J.A.R.V.I.S. SYSTEM CONVERGENCE — v2.0") 
    logger.info("   Hands-free voice: say \"Jarvis, cpu usage\"") 
    logger.info("   Follow-up window: 10 seconds after response") 
    logger.info("============================================\n")
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
    venv_dir = os.path.join(INSTALLER_DIR, "venv")
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
    reqs_path = os.path.join(INSTALLER_DIR, "voice_assistant", "requirements.txt")
    if os.path.exists(reqs_path):
        result = subprocess.run([pip_path, "install", "-r", reqs_path])
        if result.returncode != 0:
            logger.warning("Some core packages failed to install. Trying individual installs...")
            with open(reqs_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        pkg = line.split("#")[0].strip().split(">=")[0].split("==")[0].strip()
                        if pkg:
                            subprocess.run([pip_path, "install", pkg])
    else:
        logger.warning(f"Could not find requirements at {reqs_path}")

    # Install optional native-compiled packages (best-effort)
    logger.info("Installing optional system-control packages (best-effort)...")
    optional_pkgs = ["pyaudio", "pynput"]
    for pkg in optional_pkgs:
        result = subprocess.run([pip_path, "install", pkg])
        if result.returncode == 0:
            logger.info(f"  ✓ {pkg} installed successfully")
        else:
            logger.info(f"  - {pkg} skipped (not available on this system — this is OK)")

    # Ensure Flask is installed
    logger.info("Installing Flask web server...")
    subprocess.run([pip_path, "install", "flask"], check=True)

    # Step 4: Write default configuration
    setup_config_file()

    # Step 5: Install systemd service (Linux only)
    if os_name == "Linux":
        setup_systemd_service()

    # Step 6: Print service management instructions
    if os_name == "Linux":
        print()
        logger.info("=== J.A.R.V.I.S. SYSTEMD SERVICE ===")
        logger.info("INSTALLED! Manage with:")
        logger.info("  systemctl --user start jarvis      # Start server")
        logger.info("  systemctl --user stop jarvis       # Stop server")
        logger.info("  systemctl --user restart jarvis    # Restart after pull")
        logger.info("  systemctl --user enable jarvis     # Auto-start on login")
        logger.info("  journalctl --user -u jarvis -f     # View live logs")
        logger.info("==================================")
        print()

    # Step 7: Boot J.A.R.V.I.S.!
    logger.info("Setup complete! Initializing J.A.R.V.I.S. Core Web HUD...")
    server_path = os.path.join(INSTALLER_DIR, "voice_assistant", "web_server.py")

    try:
        subprocess.run([python_path, server_path])
    except KeyboardInterrupt:
        logger.info("J.A.R.V.I.S. server shut down by user request.")


if __name__ == "__main__":
    main()
