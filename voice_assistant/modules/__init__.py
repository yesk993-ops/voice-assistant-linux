"""
Voice Assistant Modules Package
"""

from .speech import SpeechRecognizer, WakeWordDetector
from .tts import TextToSpeech, TTSManager
from .power import PowerManager, PowerProfileManager
from .apps import ApplicationLauncher, ProcessManager
from .files import FileSystemManager
from .system_settings import SystemSettingsManager
from .system_commands import SystemCommandsManager
from .system_monitor import SystemMonitor
from .help import HelpSystem, HelpTopic, ContextualHelp
from .command_parser import CommandParser, ParsedCommand, IntentType

__all__ = [
    "SpeechRecognizer",
    "WakeWordDetector",
    "TextToSpeech",
    "TTSManager",
    "PowerManager",
    "PowerProfileManager",
    "ApplicationLauncher",
    "ProcessManager",
    "FileSystemManager",
    "SystemSettingsManager",
    "SystemCommandsManager",
    "SystemMonitor",
    "HelpSystem",
    "HelpTopic",
    "ContextualHelp",
    "CommandParser",
    "ParsedCommand",
    "IntentType",
]