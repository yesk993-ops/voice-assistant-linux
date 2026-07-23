"""
Help System Module
Provides tutorials, troubleshooting tips, command reference, and interactive help
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class HelpTopic:
    """Help topic structure"""
    id: str
    title: str
    description: str
    category: str
    content: str
    examples: List[str]
    related: List[str]
    tags: List[str]


class HelpSystem:
    """Provides help, tutorials, and troubleshooting"""
    
    def __init__(self):
        self.topics = {}
        self.categories = {}
        self._load_builtin_help()
        logger.info("HelpSystem initialized")
    
    def _load_builtin_help(self):
        """Load built-in help topics"""
        
        # Define all help topics
        topics = [
            HelpTopic(
                id="getting_started",
                title="Getting Started",
                description="Basic introduction to the voice assistant",
                category="basics",
                content="""
Welcome to the Linux Voice Assistant! This assistant helps you control your Linux system using voice commands.

BASIC USAGE:
1. Say the wake word (default: "assistant") or run without wake word
2. Speak your command naturally
3. The assistant will execute and respond

EXAMPLE COMMANDS:
• "Open Firefox" - Launch web browser
• "Set volume to 50 percent" - Adjust volume
• "What's my CPU usage?" - Check system stats
• "Create a folder called projects" - File management
• "Shutdown in 5 minutes" - Schedule shutdown

TIPS:
• Speak clearly and at normal pace
• Use natural language - no need for exact syntax
• Say "help" anytime for command reference
• Say "tutorial" for guided walkthrough
                """,
                examples=[
                    "assistant, open terminal",
                    "what is my memory usage",
                    "create file notes.txt with content hello world",
                    "set brightness to 70 percent"
                ],
                related=["commands", "wake_word", "configuration"],
                tags=["beginner", "intro", "basics"]
            ),
            
            HelpTopic(
                id="commands",
                title="Command Reference",
                description="Complete list of available voice commands",
                category="reference",
                content="""
POWER MANAGEMENT:
• "shutdown" / "power off" - Shutdown system
• "reboot" / "restart" - Restart system
• "suspend" / "sleep" - Suspend to RAM
• "hibernate" - Hibernate to disk
• "lock screen" - Lock the screen
• "logout" - Log out current user
• "shutdown in 10 minutes" - Schedule shutdown
• "cancel shutdown" - Cancel scheduled shutdown

APPLICATIONS:
• "open browser" / "open firefox" - Launch web browser
• "open terminal" - Launch terminal
• "open files" / "open file manager" - Launch file manager
• "open editor" / "open text editor" - Launch text editor
• "open code" / "open vscode" - Launch VS Code
• "open [app name]" - Launch any application
• "close [app name]" - Close application

FILE MANAGEMENT:
• "create file [name] with content [text]" - Create file
• "create folder [name]" - Create directory
• "delete file [name]" - Delete file
• "delete folder [name]" - Delete directory
• "copy [source] to [destination]" - Copy file/folder
• "move [source] to [destination]" - Move/rename
• "rename [old] to [new]" - Rename file/folder
• "list [directory]" - List directory contents
• "find [pattern]" - Search for files
• "read file [name]" - Read file contents
• "current directory" - Show current path

SYSTEM SETTINGS:
• "set brightness to 50" - Set screen brightness (0-100)
• "increase brightness" / "decrease brightness" - Adjust brightness
• "set volume to 70" - Set system volume (0-100)
• "increase volume" / "decrease volume" - Adjust volume
• "mute" / "unmute" - Toggle mute
• "set resolution 1920x1080" - Set screen resolution
• "list resolutions" - Show available resolutions

SYSTEM COMMANDS:
• "update system" - Run system updates
• "run command [command]" - Execute shell command
• "uptime" - Show system uptime
• "who is logged in" - Show logged in users
• "failed services" - Show failed systemd services

SYSTEM MONITORING:
• "cpu usage" - Show CPU usage
• "memory usage" / "ram usage" - Show memory usage
• "disk usage" - Show disk usage
• "temperature" - Show system temperatures
• "battery" - Show battery status
• "network info" - Show network information
• "top processes" - Show top CPU processes
• "system summary" - Complete system overview

HELP & SUPPORT:
• "help" - Show this help
• "help [topic]" - Help on specific topic
• "tutorial" - Interactive tutorial
• "commands" - List all commands
• "troubleshoot [issue]" - Troubleshooting tips
                """,
                examples=[
                    "help shutdown",
                    "tutorial",
                    "list commands"
                ],
                related=["getting_started", "troubleshooting"],
                tags=["reference", "commands", "complete"]
            ),
            
            HelpTopic(
                id="power_management",
                title="Power Management",
                description="Control system power states",
                category="system",
                content="""
POWER COMMANDS:

Shutdown:
  "shutdown" - Immediate shutdown
  "shutdown in 5 minutes" - Schedule shutdown
  "shutdown at 22:00" - Shutdown at specific time
  "cancel shutdown" - Cancel scheduled shutdown

Reboot:
  "reboot" - Immediate restart
  "reboot in 10 minutes" - Scheduled restart

Sleep/Suspend:
  "suspend" - Sleep (RAM powered)
  "hibernate" - Hibernate (saved to disk)

Security:
  "lock screen" - Lock current session
  "logout" - End current session

NOTES:
• Scheduled shutdowns require sudo privileges
• Hibernate requires swap partition >= RAM
• Some commands may prompt for password
• Use "cancel shutdown" to abort scheduled actions

EXAMPLES:
• "shutdown in 30 minutes"
• "reboot now"
• "suspend the computer"
• "lock my screen"
                """,
                examples=[
                    "shutdown in 10 minutes",
                    "reboot",
                    "suspend",
                    "lock screen"
                ],
                related=["system_commands", "troubleshooting"],
                tags=["power", "shutdown", "reboot", "suspend"]
            ),
            
            HelpTopic(
                id="file_management",
                title="File Management",
                description="Create, delete, copy, move, and manage files",
                category="files",
                content="""
FILE OPERATIONS:

Creating:
  "create file notes.txt with content Hello World"
  "create folder projects"
  "create folder documents/work"

Reading:
  "read file notes.txt"
  "read file /home/user/document.txt"
  "show me the current directory"

Listing:
  "list files" - Current directory
  "list folder downloads" - Specific directory
  "list all files" - Include hidden files
  "list details" - Detailed view with sizes

Searching:
  "find files named report"
  "find pdf files in documents"
  "search for *.py files"

Copying/Moving:
  "copy file.txt to backup.txt"
  "copy folder photos to pictures"
  "move download.zip to documents"
  "rename oldname.txt to newname.txt"

Deleting:
  "delete file temp.txt"
  "delete folder old_project"
  "delete folder old_project force" - Recursive delete

NAVIGATION:
  "go to home directory"
  "go to downloads"
  "current directory"

TIPS:
• Use relative paths (downloads/file.txt) or absolute (/home/user/file.txt)
• Say "force" for recursive directory deletion
• Tab completion works in terminal commands
• "list details" shows permissions, sizes, dates

EXAMPLES:
• "create file todo.txt with content Buy milk"
• "copy documents to backup"
• "find all jpg files"
• "delete folder temp force"
                """,
                examples=[
                    "create file test.txt with content hello",
                    "create folder projects",
                    "list files in downloads",
                    "find pdf files",
                    "copy file.txt to backup.txt"
                ],
                related=["system_commands", "troubleshooting"],
                tags=["files", "directories", "copy", "move", "delete"]
            ),
            
            HelpTopic(
                id="system_settings",
                title="System Settings",
                description="Control brightness, volume, display resolution",
                category="settings",
                content="""
DISPLAY SETTINGS:

Brightness:
  "set brightness to 50" - Set percentage (0-100)
  "increase brightness" - Increase by 10%
  "decrease brightness" - Decrease by 10%
  "brightness" - Show current brightness

Resolution:
  "set resolution 1920x1080" - Set specific resolution
  "list resolutions" - Show available resolutions
  "best resolution" - Set to native resolution

AUDIO SETTINGS:

Volume:
  "set volume to 70" - Set percentage (0-100)
  "increase volume" - Increase by 10%
  "decrease volume" - Decrease by 10%
  "volume" - Show current volume
  "mute" - Mute audio
  "unmute" - Unmute audio

NOTES:
• Brightness control requires appropriate drivers (intel_backlight, amdgpu_bl, etc.)
• Volume uses PulseAudio/PipeWire (pactl) or ALSA (amixer) fallback
• Resolution changes use xrandr - may not persist after reboot
• Some laptops need special kernel parameters for brightness

EXAMPLES:
• "set brightness to 80"
• "turn up the volume"
• "mute sound"
• "set resolution to 1920 by 1080"
• "what is my screen brightness"
                """,
                examples=[
                    "set brightness to 50",
                    "increase volume",
                    "mute",
                    "list resolutions"
                ],
                related=["troubleshooting"],
                tags=["brightness", "volume", "resolution", "display", "audio"]
            ),
            
            HelpTopic(
                id="system_monitoring",
                title="System Monitoring",
                description="Check CPU, memory, disk, temperature, and network",
                category="monitoring",
                content="""
MONITORING COMMANDS:

CPU:
  "cpu usage" - Overall CPU usage
  "cpu details" - Per-core usage
  "load average" - System load

Memory:
  "memory usage" - RAM usage
  "swap usage" - Swap usage
  "ram" - Quick memory check

Disk:
  "disk usage" - All mounted filesystems
  "disk usage root" - Specific partition
  "disk io" - Read/write statistics

Temperature:
  "temperature" - All sensors
  "cpu temperature" - CPU temps only
  "fan speed" - Fan RPM

Battery:
  "battery" - Battery status
  "battery percentage" - Quick percentage

Network:
  "network info" - Interface details
  "network speed" - Current transfer rate
  "ip address" - Show IP addresses

Processes:
  "top processes" - Top 10 by CPU
  "top memory" - Top 10 by memory
  "processes" - Process list

System Summary:
  "system summary" - Complete overview
  "system info" - Hardware/OS info

EXAMPLES:
• "how is my cpu doing"
• "show memory usage"
• "check disk space"
• "what's the temperature"
• "network speed"
• "full system report"
                """,
                examples=[
                    "cpu usage",
                    "memory usage",
                    "disk usage",
                    "temperature",
                    "battery status",
                    "system summary"
                ],
                related=["troubleshooting", "system_commands"],
                tags=["cpu", "memory", "disk", "temperature", "network", "monitoring"]
            ),
            
            HelpTopic(
                id="troubleshooting",
                title="Troubleshooting",
                description="Common issues and solutions",
                category="support",
                content="""
COMMON ISSUES:

Speech Recognition Not Working:
1. Check microphone: "arecord -l" to list devices
2. Test: "python -m speech_recognition"
3. Adjust sensitivity: Set SPEECH_ENERGY_THRESHOLD in config
4. Try different engine: Google, Vosk (offline), Whisper

Text-to-Speech Not Working:
1. Check audio output: "speaker-test -t wav"
2. Install TTS: pip install pyttsx3
3. Try espeak: sudo apt install espeak
4. Check PulseAudio: pulseaudio --check

Brightness Control Not Working:
1. Check backlight device: ls /sys/class/backlight/
2. Set BRIGHTNESS_DEVICE in config (e.g., intel_backlight, amdgpu_bl0)
3. Add kernel param: acpi_backlight=vendor
4. Install brightnessctl: sudo apt install brightnessctl

Volume Control Not Working:
1. Check PulseAudio: pactl info
2. Install pavucontrol for GUI
3. Try ALSA: amixer scontrols
4. Set ALSA_CARD and ALSA_CONTROL in config

Application Won't Launch:
1. Check command exists: which firefox
2. Try full path: /usr/bin/firefox
3. Check .desktop files in /usr/share/applications
4. Set BROWSER_COMMAND, TERMINAL_COMMAND in config

Permission Errors:
1. Some commands need sudo (shutdown, updates)
2. Configure sudoers for passwordless specific commands
3. Check user groups: groups $USER

Wake Word Not Detected:
1. Check USE_WAKE_WORD in config
2. Adjust microphone sensitivity
3. Try Porcupine for better wake word detection
4. Speak closer to microphone

Performance Issues:
1. Use lighter speech engine (Vosk offline)
2. Reduce TTS quality/speed
3. Close unnecessary applications
4. Check system resources: "system summary"

GETTING HELP:
• "help troubleshooting" - This guide
• "tutorial" - Interactive walkthrough
• Check logs: ~/.voice_assistant.log
• Run tests: python main.py --test
                """,
                examples=[
                    "troubleshoot microphone",
                    "troubleshoot brightness",
                    "help troubleshooting"
                ],
                related=["getting_started", "configuration"],
                tags=["troubleshooting", "issues", "fix", "debug"]
            ),
            
            HelpTopic(
                id="configuration",
                title="Configuration",
                description="Customize the assistant for your system",
                category="setup",
                content="""
CONFIGURATION FILE:

The assistant uses environment variables for configuration.
Create a .env file or set environment variables:

SPEECH RECOGNITION:
  SPEECH_RECOGNITION_ENGINE=google|vosk|whisper|sphinx
  SPEECH_LANGUAGE=en-US
  SPEECH_TIMEOUT=5
  SPEECH_ENERGY_THRESHOLD=300
  VOSK_MODEL_PATH=/path/to/vosk/model
  WHISPER_MODEL=base

TEXT-TO-SPEECH:
  TTS_ENGINE=pyttsx3|gtts|espeak|festival
  TTS_RATE=180
  TTS_VOLUME=1.0
  TTS_VOICE=voice_id
  TTS_LANGUAGE=en

WAKE WORD:
  WAKE_WORD=assistant
  USE_WAKE_WORD=true|false
  PORCUPINE_ACCESS_KEY=your_key

APPLICATIONS:
  BROWSER_COMMAND=firefox
  TERMINAL_COMMAND=gnome-terminal
  FILE_MANAGER_COMMAND=nautilus
  TEXT_EDITOR_COMMAND=gedit
  CODE_EDITOR_COMMAND=code

SYSTEM COMMANDS:
  SHUTDOWN_COMMAND=systemctl poweroff
  REBOOT_COMMAND=systemctl reboot
  SUSPEND_COMMAND=systemctl suspend
  LOCK_COMMAND=gnome-screensaver-command -l
  UPDATE_COMMAND=sudo apt update && sudo apt upgrade -y

HARDWARE:
  BRIGHTNESS_DEVICE=intel_backlight
  ALSA_CARD=default
  ALSA_CONTROL=Master
  NETWORK_INTERFACE=auto

LOGGING:
  LOG_LEVEL=INFO|DEBUG|WARNING
  LOG_FILE=voice_assistant.log

EXAMPLE .env FILE:
  SPEECH_RECOGNITION_ENGINE=vosk
  VOSK_MODEL_PATH=/usr/share/vosk/model
  TTS_ENGINE=pyttsx3
  WAKE_WORD=computer
  USE_WAKE_WORD=true
  BRIGHTNESS_DEVICE=amdgpu_bl0
  BROWSER_COMMAND=brave-browser

DESKTOP ENVIRONMENT DETECTION:
The assistant auto-detects GNOME, KDE, XFCE, etc. and adjusts commands.
Override with specific commands if needed.
                """,
                examples=[],
                related=["getting_started", "troubleshooting"],
                tags=["config", "setup", "environment", "customization"]
            ),
            
            HelpTopic(
                id="tutorial",
                title="Interactive Tutorial",
                description="Step-by-step guide to using the voice assistant",
                category="basics",
                content="""
INTERACTIVE TUTORIAL

Welcome! Let's walk through the basics.

STEP 1: Wake Word (if enabled)
Say "assistant" or your configured wake word.
The assistant will respond "Yes?" ready for your command.

STEP 2: Basic Commands
Try these:
• "What time is it?"
• "Open terminal"
• "Set volume to 50"

STEP 3: System Information
• "CPU usage"
• "Memory usage"
• "Disk usage"
• "Battery status"

STEP 4: File Operations
• "Create folder test_folder"
• "Create file hello.txt with content Hello World"
• "List files"
• "Read file hello.txt"

STEP 5: System Control
• "Set brightness to 70"
• "Mute volume"
• "Lock screen"

STEP 6: Advanced
• "Run command ls -la"
• "Update system"
• "Top processes"

PRACTICE EXERCISES:
1. Create a folder called "voice_test" in your home directory
2. Create a file "notes.txt" inside it with some text
3. Read the file back
4. Check your system temperature
5. Set volume to 30%

TIPS FOR SUCCESS:
• Speak naturally - no need for robotic speech
• Pause briefly after wake word
• Use "help" anytime you're stuck
• Commands are case-insensitive
• Try variations: "open browser" = "launch firefox" = "start chrome"

NEXT STEPS:
• Explore "help commands" for full reference
• Customize settings in .env file
• Try offline speech recognition (Vosk)
• Set up wake word detection (Porcupine)

Say "tutorial" anytime to restart this guide!
                """,
                examples=[
                    "tutorial",
                    "help tutorial"
                ],
                related=["getting_started", "commands"],
                tags=["tutorial", "guide", "walkthrough", "beginner"]
            ),
        ]
        
        for topic in topics:
            self.topics[topic.id] = topic
            if topic.category not in self.categories:
                self.categories[topic.category] = []
            self.categories[topic.category].append(topic.id)
    
    def show_help(self, topic: str = "") -> str:
        """Show help for topic or general help"""
        if not topic:
            return self._general_help()
        
        topic = topic.lower().replace(" ", "_")
        
        if topic in self.topics:
            return self._format_topic(self.topics[topic])
        
        # Search for partial matches
        matches = [t for t in self.topics if topic in t.lower()]
        if matches:
            if len(matches) == 1:
                return self._format_topic(self.topics[matches[0]])
            else:
                return f"Multiple topics match '{topic}':\n" + "\n".join(f"  • {m}" for m in matches)
        
        return f"Help topic not found: {topic}\n\n{self._general_help()}"
    
    def _general_help(self) -> str:
        """Show general help overview"""
        lines = [
            "=" * 50,
            "LINUX VOICE ASSISTANT - HELP",
            "=" * 50,
            "",
            "Say 'help [topic]' for detailed information.",
            "",
            "CATEGORIES:"
        ]
        
        for cat, topics in self.categories.items():
            lines.append(f"\n  {cat.upper()}:")
            for t_id in topics:
                topic = self.topics[t_id]
                lines.append(f"    • {topic.title} (help {t_id})")
        
        lines.extend([
            "",
            "QUICK START:",
            "  • Say 'tutorial' for interactive guide",
            "  • Say 'commands' for full command list",
            "  • Say 'troubleshoot [issue]' for help",
            "",
            "EXAMPLES:",
            "  help getting_started",
            "  help file_management",
            "  help system_settings",
            "  troubleshoot microphone",
        ])
        
        return "\n".join(lines)
    
    def _format_topic(self, topic: HelpTopic) -> str:
        """Format a help topic for display"""
        lines = [
            "=" * 50,
            f"{topic.title.upper()}",
            "=" * 50,
            "",
            topic.content.strip(),
        ]
        
        if topic.examples:
            lines.extend(["", "EXAMPLES:"])
            for ex in topic.examples:
                lines.append(f"  • \"{ex}\"")
        
        if topic.related:
            lines.extend(["", "RELATED TOPICS:"])
            for rel in topic.related:
                lines.append(f"  • help {rel}")
        
        return "\n".join(lines)
    
    def show_command_help(self, command: str) -> str:
        """Show help for specific command"""
        command = command.lower()
        
        # Map commands to help topics
        command_map = {
            "shutdown": "power_management",
            "reboot": "power_management",
            "suspend": "power_management",
            "hibernate": "power_management",
            "lock": "power_management",
            "logout": "power_management",
            "browser": "commands",
            "terminal": "commands",
            "file": "file_management",
            "folder": "file_management",
            "copy": "file_management",
            "move": "file_management",
            "delete": "file_management",
            "rename": "file_management",
            "list": "file_management",
            "find": "file_management",
            "read": "file_management",
            "brightness": "system_settings",
            "volume": "system_settings",
            "resolution": "system_settings",
            "mute": "system_settings",
            "cpu": "system_monitoring",
            "memory": "system_monitoring",
            "disk": "system_monitoring",
            "temperature": "system_monitoring",
            "battery": "system_monitoring",
            "network": "system_monitoring",
            "process": "system_monitoring",
            "update": "system_commands",
            "uptime": "system_commands",
        }
        
        for key, topic_id in command_map.items():
            if key in command:
                return self._format_topic(self.topics[topic_id])
        
        return f"No specific help for '{command}'. Try 'help commands' for full list."
    
    def list_commands(self) -> str:
        """List all available commands"""
        return self.show_help("commands")
    
    def show_tutorial(self) -> str:
        """Show interactive tutorial"""
        return self.show_help("tutorial")
    
    def search_help(self, query: str) -> str:
        """Search help topics"""
        query = query.lower()
        results = []
        
        for topic in self.topics.values():
            score = 0
            if query in topic.id.lower():
                score += 10
            if query in topic.title.lower():
                score += 8
            if query in topic.description.lower():
                score += 5
            if query in topic.content.lower():
                score += 3
            if any(query in tag for tag in topic.tags):
                score += 5
            
            if score > 0:
                results.append((score, topic))
        
        if not results:
            return f"No help topics found for '{query}'"
        
        results.sort(key=lambda x: x[0], reverse=True)
        lines = [f"Search results for '{query}':"]
        for score, topic in results[:10]:
            lines.append(f"  • {topic.title} (help {topic.id}) - {topic.description}")
        
        return "\n".join(lines)
    
    def get_category(self, category: str) -> List[HelpTopic]:
        """Get all topics in a category"""
        topic_ids = self.categories.get(category.lower(), [])
        return [self.topics[t_id] for t_id in topic_ids]
    
    def test(self) -> bool:
        """Test help system"""
        try:
            self.show_help()
            self.show_help("getting_started")
            self.search_help("volume")
            self.show_command_help("shutdown")
            logger.info("Help system test passed")
            return True
        except Exception as e:
            logger.error(f"Help system test failed: {e}")
            return False


class ContextualHelp:
    """Provides contextual help based on current state"""
    
    def __init__(self, help_system: HelpSystem):
        self.help = help_system
        self.context_stack = []
    
    def push_context(self, context: str):
        """Push context onto stack"""
        self.context_stack.append(context)
    
    def pop_context(self) -> Optional[str]:
        """Pop context from stack"""
        if self.context_stack:
            return self.context_stack.pop()
        return None
    
    def get_contextual_help(self, user_input: str = "") -> str:
        """Get help based on current context and input"""
        if not self.context_stack:
            return self.help.show_help()
        
        current = self.context_stack[-1]
        
        # Context-specific help
        context_help = {
            "file_operations": "file_management",
            "system_settings": "system_settings",
            "monitoring": "system_monitoring",
            "power": "power_management",
        }
        
        if current in context_help:
            return self.help.show_help(context_help[current])
        
        return self.help.show_help()