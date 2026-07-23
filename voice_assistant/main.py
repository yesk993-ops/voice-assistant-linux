"""
Voice Assistant for Linux System Control
Main entry point and core assistant logic
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json

# Ensure the project root is on sys.path for correct imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Load configuration
from dotenv import load_dotenv
load_dotenv(os.path.join(_project_root, "config", "config.env"))

# Import modules
from voice_assistant.modules.speech import SpeechRecognizer
from voice_assistant.modules.tts import TextToSpeech
from voice_assistant.modules.power import PowerManager
from voice_assistant.modules.apps import ApplicationLauncher
from voice_assistant.modules.files import FileSystemManager
from voice_assistant.modules.system_settings import SystemSettingsManager
from voice_assistant.modules.system_commands import SystemCommandsManager
from voice_assistant.modules.system_monitor import SystemMonitor
from voice_assistant.modules.help import HelpSystem
from voice_assistant.modules.command_parser import CommandParser
from voice_assistant.modules.response_formatter import (
    ResponseFormatter, QueryClassifier, StructuredResponse,
    ResponseType, Verbosity
)

logger = logging.getLogger(__name__)


class AssistantState(Enum):
    """Assistant operational states"""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class Command:
    """Parsed command structure"""
    intent: str
    entities: Dict[str, Any]
    raw_text: str
    confidence: float


class VoiceAssistant:
    """Main Voice Assistant class for Linux system control"""

    # Destructive commands that require user confirmation
    DESTRUCTIVE_COMMANDS = {
        "shutdown", "reboot", "suspend", "hibernate", "logout",
        "delete_file", "delete_directory",
    }

    # Status commands that should get brief answers
    STATUS_COMMANDS = {
        "get_brightness", "get_volume", "get_cpu_usage", "get_memory_usage",
        "get_disk_usage", "get_temperature", "get_battery", "get_network_info",
        "show_uptime", "show_users", "system_summary",
    }

    def __init__(self, config_path: str = None):
        """Initialize the voice assistant with all modules"""
        if config_path is None:
            config_path = os.path.join(_project_root, "config", "config.env")
        self.config_path = config_path
        self.state = AssistantState.IDLE
        self.running = False
        self.wake_word_active = False
        self._pending_confirmation = None  # For destructive action confirmation
        
        # Conversational memory (Gemini-style follow-up context)
        self.conversation_history = []  # Max 5 entries
        self._last_intent = None
        self._last_text = None
        self._last_response = None
        self._last_entities = {}
        
        # Conversational memory (Gemini-style follow-up context)
        self.conversation_history: List[Dict[str, str]] = []  # Max 5 entries
        self._last_intent: Optional[str] = None
        self._last_text: Optional[str] = None
        self._last_response: Optional[str] = None
        self._last_entities: Dict[str, Any] = {}

        # Initialize logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize modules
        self._init_modules()

        # Command registry
        self.commands: Dict[str, Callable] = {}
        self._register_commands()

        logger.info("Voice Assistant initialized successfully")

    def _setup_logging(self):
        """Configure logging"""
        log_level = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "voice_assistant.log")

        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment"""
        return {
            "speech_engine": os.getenv("SPEECH_RECOGNITION_ENGINE", "google"),
            "speech_language": os.getenv("SPEECH_LANGUAGE", "en-US"),
            "speech_timeout": int(os.getenv("SPEECH_TIMEOUT", "5")),
            "tts_engine": os.getenv("TTS_ENGINE", "pyttsx3"),
            "tts_rate": int(os.getenv("TTS_RATE", "180")),
            "tts_volume": float(os.getenv("TTS_VOLUME", "1.0")),
            "wake_word": os.getenv("WAKE_WORD", "assistant"),
            "use_wake_word": os.getenv("USE_WAKE_WORD", "false").lower() == "true",
        }

    def _init_modules(self):
        """Initialize all system modules"""
        try:
            self.speech = SpeechRecognizer(
                engine=self.config["speech_engine"],
                language=self.config["speech_language"],
                timeout=self.config["speech_timeout"]
            )
            self.tts = TextToSpeech(
                engine=self.config["tts_engine"],
                rate=self.config["tts_rate"],
                volume=self.config["tts_volume"]
            )
            self.power = PowerManager()
            self.apps = ApplicationLauncher()
            self.files = FileSystemManager()
            self.settings = SystemSettingsManager()
            self.sys_commands = SystemCommandsManager()
            self.monitor = SystemMonitor()
            self.help = HelpSystem()
            self.parser = CommandParser()

            logger.info("All modules initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize modules: {e}")
            raise

    def _get_greeting_response(self) -> str:
        """Return a friendly greeting response"""
        import random
        greetings = [
            "Hey there! How can I help you today?",
            "Hi! What can I do for you?",
            "Hello! Ready to help — just say the word.",
            "Hey! What's up?",
            "Hello there! How can I assist you?",
        ]
        return random.choice(greetings)
    
    def _get_how_are_you_response(self) -> str:
        """Return a response to 'how are you'"""
        import random
        responses = [
            "I'm doing great, thanks for asking! How can I help you?",
            "All systems operational and ready to assist! What do you need?",
            "Doing well! Just waiting for your command.",
            "I'm good! What can I do for you?",
        ]
        return random.choice(responses)
    
    def _get_thanks_response(self) -> str:
        """Return a response to 'thank you'"""
        import random
        responses = [
            "You're welcome! Happy to help.",
            "Anytime! Let me know if you need anything else.",
            "Glad I could help!",
            "No problem at all!",
        ]
        return random.choice(responses)
    
    def _get_who_are_you_response(self) -> str:
        """Return a response to 'who are you'"""
        return "I'm J.A.R.V.I.S. — your voice assistant for Linux system control. I can check your system stats, manage files, control volume and brightness, launch applications, and more. Say 'help' to see everything I can do!"
    
    def _resolve_followup(self, text: str) -> str:
        """Resolve follow-up queries against last conversation context"""
        text_lower = text.lower()
        prev_intent = self._last_intent or ""
        
        # If user says "and what about X" or "how about X"
        topic_map = {
            "cpu": "cpu usage", "processor": "cpu usage", "performance": "cpu usage",
            "memory": "memory usage", "ram": "memory usage",
            "disk": "disk usage", "storage": "disk usage", "drive": "disk usage", "space": "disk usage",
            "battery": "battery", "power": "battery", "charge": "battery",
            "temp": "temperature", "temperature": "temperature", "heat": "temperature", "hot": "temperature",
            "network": "network info", "internet": "network info", "wifi": "network info", "ip": "network info",
            "volume": "volume", "sound": "volume", "audio": "volume",
            "brightness": "brightness", "screen": "brightness", "display": "brightness",
            "process": "top processes", "program": "top processes", "running": "top processes",
        }
        
        for keyword, mapped_text in topic_map.items():
            if keyword in text_lower:
                return mapped_text
        
        # Generic follow-up — user just said "and?" or "what else?" — return system summary
        if any(w in text_lower for w in ["else", "more", "other", "another", "summary", "overview"]):
            return "system summary"
        
        return ""
    
    def _update_conversation(self, text: str, intent: str, response: str):
        """Update conversational memory with latest exchange"""
        self._last_text = text
        self._last_intent = intent
        self._last_response = response
        self.conversation_history.append({"role": "user", "text": text})
        self.conversation_history.append({"role": "assistant", "text": response})
        # Keep only last 5 exchanges (10 entries)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _fallback_response(self, text: str) -> str:
        """When no intent matches, try keyword-based fallback to suggest what the user might want"""
        import random
        text_lower = text.lower()
        
        # Keyword matching for common topics
        hints = []
        
        if any(w in text_lower for w in ['cpu', 'processor', 'performance']):
            hints.append("Try saying 'cpu usage' or 'how's the cpu?'")
        elif any(w in text_lower for w in ['memory', 'ram']):
            hints.append("Try saying 'memory usage' or 'how much ram is being used?'")
        elif any(w in text_lower for w in ['disk', 'storage', 'drive', 'space']):
            hints.append("Try saying 'disk usage' or 'how much space is left?'")
        elif any(w in text_lower for w in ['battery', 'charge', 'power']):
            hints.append("Try saying 'battery status' or 'how much battery is left?'")
        elif any(w in text_lower for w in ['temperature', 'temp', 'hot']):
            hints.append("Try saying 'temperature' or 'how hot is the system?'")
        elif any(w in text_lower for w in ['network', 'internet', 'wifi', 'ip']):
            hints.append("Try saying 'network info' or 'what's my ip?'")
        elif any(w in text_lower for w in ['volume', 'sound', 'audio', 'speaker']):
            hints.append("Try saying 'set volume to 50' or 'mute' or 'volume status'")
        elif any(w in text_lower for w in ['brightness', 'screen', 'display']):
            hints.append("Try saying 'set brightness to 70' or 'brightness status'")
        elif any(w in text_lower for w in ['open', 'launch', 'start', 'run']):
            hints.append("Try saying 'open firefox', 'open terminal', or 'open calculator'")
        elif any(w in text_lower for w in ['close', 'quit', 'kill']):
            hints.append("Try saying 'close firefox' or 'quit the app'")
        elif any(w in text_lower for w in ['file', 'folder', 'directory', 'create', 'delete']):
            hints.append("Try saying 'create file test.txt', 'list files', or 'delete file old.txt'")
        elif any(w in text_lower for w in ['shutdown', 'reboot', 'restart', 'sleep']):
            hints.append("Try saying 'shutdown', 'reboot', or 'suspend'")
        elif any(w in text_lower for w in ['hello', 'hi', 'hey']):
            return "Hey there! To ask me something, just say it directly — like 'cpu usage' or 'open browser'. Try saying 'help' to see what I can do!"
        
        if hints:
            return "Hmm, I'm not sure I understood that. " + hints[0]
        
        # Completely unknown - suggest help
        confused = [
            "I didn't quite catch that. Try saying 'help' to see what I can do, or just ask me something like 'what's the cpu usage?'",
            "Not sure what you mean. Say 'help' for a list of things I can do!",
            "Hmm, I don't know that one yet. Try 'help' to see what commands I understand.",
        ]
        return random.choice(confused)
    
    def _register_commands(self):
        """Register all voice commands with their handlers"""
        self.commands = {
            # Power Management
            "shutdown": self.power.shutdown,
            "reboot": self.power.reboot,
            "suspend": self.power.suspend,
            "hibernate": self.power.hibernate,
            "lock": self.power.lock,
            "logout": self.power.logout,

            # Application Launching
            "open_browser": self.apps.open_browser,
            "open_terminal": self.apps.open_terminal,
            "open_file_manager": self.apps.open_file_manager,
            "open_text_editor": self.apps.open_text_editor,
            "open_code_editor": self.apps.open_code_editor,
            "open_application": self.apps.open_application,
            "close_application": self.apps.close_application,

            # File Management
            "create_file": self.files.create_file,
            "create_directory": self.files.create_directory,
            "delete_file": self.files.delete_file,
            "delete_directory": self.files.delete_directory,
            "copy_file": self.files.copy_file,
            "move_file": self.files.move_file,
            "rename_file": self.files.rename_file,
            "list_directory": self.files.list_directory,
            "search_files": self.files.search_files,
            "read_file": self.files.read_file,
            "write_file": self.files.write_file,
            "change_directory": self.files.change_directory,
            "get_file_info": self.files.get_file_info,
            "find_large_files": self.files.find_large_files,

            # System Settings
            "set_brightness": self.settings.set_brightness,
            "get_brightness": self.settings.get_brightness,
            "increase_brightness": self.settings.increase_brightness,
            "decrease_brightness": self.settings.decrease_brightness,
            "set_volume": self.settings.set_volume,
            "get_volume": self.settings.get_volume,
            "increase_volume": self.settings.increase_volume,
            "decrease_volume": self.settings.decrease_volume,
            "mute_volume": self.settings.mute_volume,
            "unmute_volume": self.settings.unmute_volume,
            "set_resolution": self.settings.set_resolution,
            "get_resolution": self.settings.get_resolution,
            "list_resolutions": self.settings.list_resolutions,

            # System Commands
            "run_update": self.sys_commands.run_update,
            "run_command": self.sys_commands.run_command,
            "shutdown_timer": self.sys_commands.shutdown_timer,
            "cancel_shutdown": self.sys_commands.cancel_shutdown,
            "show_uptime": self.sys_commands.show_uptime,
            "show_users": self.sys_commands.show_users,

            # System Monitoring
            "get_cpu_usage": self.monitor.get_cpu_usage,
            "get_memory_usage": self.monitor.get_memory_usage,
            "get_disk_usage": self.monitor.get_disk_usage,
            "get_temperature": self.monitor.get_temperature,
            "get_battery": self.monitor.get_battery,
            "get_network_info": self.monitor.get_network_info,
            "get_processes": self.monitor.get_top_processes,
            "system_summary": self.monitor.get_system_summary,

            # Help System
            "show_help": self.help.show_help,
            "show_command_help": self.help.show_command_help,
            "list_commands": self.help.list_commands,
            "show_tutorial": self.help.show_tutorial,
            "search_help": self.help.search_help,
            
            # Greetings / Chitchat
            "greeting": self._get_greeting_response,
            "how_are_you": self._get_how_are_you_response,
            "thanks": self._get_thanks_response,
            "who_are_you": self._get_who_are_you_response,
        }

    def speak(self, text: str, suppress_long: bool = True):
        """Speak text using TTS, with optional suppression for long text"""
        self.state = AssistantState.SPEAKING

        if suppress_long and len(text) > 200:
            # For long responses, speak a summary instead
            sentences = text.replace('\n', '. ').split('.')
            short = ' '.join(s.strip() for s in sentences[:2] if len(s.strip()) > 5)
            if short:
                logger.info(f"TTS suppressed long text ({len(text)} chars). Speaking: {short}...")
                self.tts.speak(short + ".")
                self.state = AssistantState.IDLE
                return

        logger.info(f"Speaking: {text[:100]}...")
        self.tts.speak(text)
        self.state = AssistantState.IDLE

    def listen(self) -> Optional[str]:
        """Listen for voice input"""
        self.state = AssistantState.LISTENING
        logger.info("Listening...")
        text = self.speech.listen()
        self.state = AssistantState.IDLE
        return text

    def process_command(self, text: str) -> str:
        """Process voice command and execute with structured responses"""
        self.state = AssistantState.PROCESSING
        logger.info(f"Processing: {text}")

        # Handle confirmation responses for destructive actions
        if self._pending_confirmation:
            result = self._handle_confirmation(text)
            self._update_conversation(text, "confirmation", result)
            return result

        # Detect follow-up context (Gemini-style: "and what about memory?")
        text_lower = text.lower().strip()
        is_followup = any(w in text_lower for w in ["and", "what about", "how about", "what's", "how's", "tell me"])
        has_topic = any(w in text_lower for w in ["cpu", "memory", "ram", "disk", "battery", "temp", "network", "process", "volume", "brightness"])
        
        # Parse command
        command = self.parser.parse(text)

        # If intent is unknown but we have context and this looks like a follow-up
        if command.intent == "unknown" and self._last_intent and (is_followup or has_topic):
            context_intent = self._resolve_followup(text_lower)
            if context_intent:
                logger.info(f"Follow-up detected: '{text}' -> {context_intent} (from previous: {self._last_intent})")
                command = self.parser.parse(context_intent)

        if command.intent not in self.commands:
            fallback_msg = self._fallback_response(text)
            response = ResponseFormatter.info(fallback_msg)
            self.state = AssistantState.IDLE
            final_response = self._format_final_response(response, command.intent, text)
            self._update_conversation(text, command.intent, final_response)
            return final_response

        # Classify the query for appropriate response style
        response_type = QueryClassifier.classify(command.intent, text)
        verbosity = QueryClassifier.verbosity_for(command.intent, text)

        # Check if confirmation is needed for destructive commands
        if QueryClassifier.requires_confirmation(command.intent):
            self._pending_confirmation = {
                "intent": command.intent,
                "entities": command.entities,
                "handler": self.commands[command.intent],
                "action_name": command.intent.replace("_", " ").title()
            }
            confirm = ResponseFormatter.confirmation(
                f"Are you sure you want to {command.intent.replace('_', ' ')}? Say 'yes' to confirm or 'no' to cancel.",
                command.intent
            )
            self.state = AssistantState.IDLE
            return confirm.message

        try:
            # Execute command with the raw handler
            handler = self.commands[command.intent]
            raw_result = handler(**command.entities)

            # Wrap the raw string result into a StructuredResponse
            if isinstance(raw_result, str):
                if response_type == ResponseType.STATUS:
                    response = ResponseFormatter.status(raw_result)
                elif not raw_result.lower().startswith("failed") and not raw_result.lower().startswith("error"):
                    response = ResponseFormatter.success(raw_result)
                else:
                    response = ResponseFormatter.error(raw_result, details=raw_result)
            elif isinstance(raw_result, StructuredResponse):
                response = raw_result
            elif isinstance(raw_result, dict):
                response = ResponseFormatter.info(
                    raw_result.get("message", str(raw_result)),
                    data=raw_result
                )
            else:
                response = ResponseFormatter.info(str(raw_result))

        except TypeError as e:
            logger.error(f"Command parameter error: {e}")
            response = ResponseFormatter.error(
                f"Invalid parameters for {command.intent}. Try 'help {command.intent}' for usage.",
                error_code="INVALID_PARAMS",
                details=str(e)
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            response = ResponseFormatter.error(
                f"Error executing {command.intent}: {str(e)}",
                error_code="EXECUTION_ERROR",
                details=str(e)
            )

        self.state = AssistantState.IDLE
        final_response = self._format_final_response(response, command.intent, text)
        
        # Store in conversation memory
        self._update_conversation(text, command.intent, final_response)
        
        return final_response

    def _handle_confirmation(self, text: str) -> str:
        """Handle user's confirmation response for destructive actions"""
        text_lower = text.lower().strip()
        pending = self._pending_confirmation
        self._pending_confirmation = None

        if pending is None:
            return "No action pending confirmation."

        # Check for affirmative responses
        affirmative = {"yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "do it", "go ahead"}
        negative = {"no", "nope", "cancel", "stop", "don't", "abort", "never mind"}

        if text_lower in affirmative:
            try:
                handler = pending["handler"]
                entities = pending.get("entities", {})
                raw_result = handler(**entities)
                response_text = raw_result if isinstance(raw_result, str) else str(raw_result)
                return response_text
            except Exception as e:
                logger.error(f"Confirmed action failed: {e}")
                action_name = pending.get("action_name", "action")
                return f"Failed to execute {action_name}: {str(e)}"
        elif text_lower in negative:
            action_name = pending.get("action_name", "action")
            return f"{action_name} cancelled."
        else:
            # Ask again more clearly
            self._pending_confirmation = pending
            action_name = pending.get("action_name", "action")
            return f"Please say 'yes' to confirm {action_name}, or 'no' to cancel."

    def _format_final_response(self, response: StructuredResponse, intent: str, raw_text: str) -> str:
        """Format the final response string, applying verbosity and TTS rules"""
        verbosity = QueryClassifier.verbosity_for(intent, raw_text)
        formatted = ResponseFormatter.format(response, verbosity)

        # Log the response quality for diagnostics
        if not formatted.success:
            logger.warning(f"Command failed: {formatted.error_code}: {formatted.error_details}")

        # For system info responses, store data for potential follow-up
        if formatted.type == ResponseType.SYSTEM_INFO and formatted.data:
            self._last_response_data = formatted.data

        # If TTS is suppressed, add a note to the spoken version
        if formatted.tts_suppressed:
            logger.info(f"TTS suppressed for long response ({len(formatted.message)} chars)")

        return formatted.message

    def run_once(self):
        """Run a single listen-process-speak cycle"""
        text = self.listen()
        if text:
            response = self.process_command(text)
            self.speak(response)

    def run_continuous(self):
        """Run continuous listening loop with adaptive responses"""
        self.running = True
        self.wake_word_active = self.config["use_wake_word"]

        self.speak("Voice assistant started. Say 'help' for commands.")
        logger.info("Starting continuous listening loop")

        while self.running:
            try:
                if self.wake_word_active:
                    text = self.speech.listen_for_wake_word(self.config["wake_word"])
                    if text:
                        # Strip the wake word from the detected text
                        wake_word = self.config["wake_word"].lower()
                        command_text = text.lower().replace(wake_word, "", 1).strip()
                        # Clean up leading punctuation/spaces
                        command_text = command_text.lstrip(" ,.!?:;")

                        if command_text:
                            # User said wake word + command in one utterance
                            logger.info(f"Wake word + command detected: {command_text}")
                            response = self.process_command(command_text)
                            self.speak(response)
                        else:
                            # Only the wake word was said — listen for the actual command
                            self.speak("Yes?")
                            command_text = self.listen()
                            if command_text:
                                response = self.process_command(command_text)
                                self.speak(response)
                else:
                    text = self.listen()
                    if text:
                        response = self.process_command(text)
                        self.speak(response)

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                self.speak("An error occurred. Continuing...")

        self.speak("Voice assistant stopped.")

    def stop(self):
        """Stop the assistant"""
        self.running = False
        logger.info("Assistant stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get assistant status"""
        return {
            "state": self.state.value,
            "running": self.running,
            "wake_word_active": self.wake_word_active,
            "config": self.config
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Assistant for Linux")
    parser.add_argument("--once", action="store_true", help="Run single command cycle")
    parser.add_argument("--config", default="config/config.env", help="Config file path")
    parser.add_argument("--test", action="store_true", help="Run module tests")
    args = parser.parse_args()

    # Create assistant
    assistant = VoiceAssistant(config_path=args.config)

    if args.test:
        # Run module tests
        test_modules(assistant)
    elif args.once:
        assistant.run_once()
    else:
        assistant.run_continuous()


def test_modules(assistant: VoiceAssistant):
    """Test all modules"""
    logger.info("Running module tests...")

    tests = [
        ("Speech Recognition", lambda: assistant.speech.test()),
        ("Text-to-Speech", lambda: assistant.tts.test()),
        ("Power Manager", lambda: assistant.power.test()),
        ("App Launcher", lambda: assistant.apps.test()),
        ("File System", lambda: assistant.files.test()),
        ("System Settings", lambda: assistant.settings.test()),
        ("System Commands", lambda: assistant.sys_commands.test()),
        ("System Monitor", lambda: assistant.monitor.test()),
        ("Help System", lambda: assistant.help.test()),
        ("Command Parser", lambda: assistant.parser.test()),
        ("Response Formatter", lambda: _test_response_formatter()),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            logger.info(f"{name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            logger.error(f"{name}: ERROR - {e}")


def _test_response_formatter() -> bool:
    """Test response formatter module"""
    try:
        # Test success response
        sr = ResponseFormatter.success("Test successful")
        assert sr.success
        assert sr.type == ResponseType.ACTION_RESULT

        # Test error response
        er = ResponseFormatter.error("Test error", error_code="TEST_ERR")
        assert not er.success
        assert er.error_code == "TEST_ERR"

        # Test confirmation
        cr = ResponseFormatter.confirmation("Are you sure?", "shutdown")
        assert cr.requires_confirmation
        assert "sure" in cr.message

        # Test destructive
        dr = ResponseFormatter.destructive("Warning!")
        assert dr.requires_confirmation

        # Test brief formatting
        long_text = "This is a very long response. " * 20
        sr_long = ResponseFormatter.info(long_text)
        formatted = ResponseFormatter.format(sr_long, Verbosity.BRIEF)
        assert len(formatted.message) < len(long_text)

        # Test TTS suppression
        sr_very_long = ResponseFormatter.info("X" * 300)
        formatted_long = ResponseFormatter.format(sr_very_long, Verbosity.DETAILED)
        assert formatted_long.tts_suppressed

        # Test query classification
        assert QueryClassifier.classify("shutdown") == ResponseType.DESTRUCTIVE
        assert QueryClassifier.classify("get_cpu_usage") == ResponseType.STATUS
        assert QueryClassifier.classify("show_help") == ResponseType.HELP

        logger.info("Response formatter test passed")
        return True
    except Exception as e:
        logger.error(f"Response formatter test failed: {e}")
        return False


if __name__ == "__main__":
    main()
