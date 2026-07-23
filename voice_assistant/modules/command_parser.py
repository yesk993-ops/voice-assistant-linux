"""
Command Parser Module
Parses natural language input into structured commands with intents and entities
"""

import os
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Supported intent types"""
    # Power
    SHUTDOWN = "shutdown"
    REBOOT = "reboot"
    SUSPEND = "suspend"
    HIBERNATE = "hibernate"
    LOCK = "lock"
    LOGOUT = "logout"
    
    # Applications
    OPEN_BROWSER = "open_browser"
    OPEN_TERMINAL = "open_terminal"
    OPEN_FILE_MANAGER = "open_file_manager"
    OPEN_TEXT_EDITOR = "open_text_editor"
    OPEN_CODE_EDITOR = "open_code_editor"
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    
    # Files
    CREATE_FILE = "create_file"
    CREATE_DIRECTORY = "create_directory"
    DELETE_FILE = "delete_file"
    DELETE_DIRECTORY = "delete_directory"
    COPY_FILE = "copy_file"
    MOVE_FILE = "move_file"
    RENAME_FILE = "rename_file"
    LIST_DIRECTORY = "list_directory"
    SEARCH_FILES = "search_files"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    CHANGE_DIRECTORY = "change_directory"
    GET_FILE_INFO = "get_file_info"
    DISK_USAGE = "get_disk_usage"
    FIND_LARGE_FILES = "find_large_files"
    
    # System Settings
    SET_BRIGHTNESS = "set_brightness"
    GET_BRIGHTNESS = "get_brightness"
    INCREASE_BRIGHTNESS = "increase_brightness"
    DECREASE_BRIGHTNESS = "decrease_brightness"
    SET_VOLUME = "set_volume"
    GET_VOLUME = "get_volume"
    INCREASE_VOLUME = "increase_volume"
    DECREASE_VOLUME = "decrease_volume"
    MUTE_VOLUME = "mute_volume"
    UNMUTE_VOLUME = "unmute_volume"
    SET_RESOLUTION = "set_resolution"
    GET_RESOLUTION = "get_resolution"
    LIST_RESOLUTIONS = "list_resolutions"
    
    # System Commands
    RUN_UPDATE = "run_update"
    RUN_COMMAND = "run_command"
    SHUTDOWN_TIMER = "shutdown_timer"
    CANCEL_SHUTDOWN = "cancel_shutdown"
    SHOW_UPTIME = "show_uptime"
    SHOW_USERS = "show_users"
    
    # System Monitoring
    GET_CPU_USAGE = "get_cpu_usage"
    GET_MEMORY_USAGE = "get_memory_usage"
    GET_DISK_USAGE = "get_disk_usage"
    GET_TEMPERATURE = "get_temperature"
    GET_BATTERY = "get_battery"
    GET_NETWORK_INFO = "get_network_info"
    GET_PROCESSES = "get_processes"
    SYSTEM_SUMMARY = "system_summary"
    
    # Help
    SHOW_HELP = "show_help"
    SHOW_COMMAND_HELP = "show_command_help"
    LIST_COMMANDS = "list_commands"
    SHOW_TUTORIAL = "show_tutorial"
    SEARCH_HELP = "search_help"
    
    # Unknown
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Parsed command result"""
    intent: str
    entities: Dict[str, Any]
    raw_text: str
    confidence: float
    original_intent: Optional[str] = None


class CommandParser:
    """Parses natural language into structured commands"""
    
    def __init__(self):
        self.patterns = self._build_patterns()
        self.entity_extractors = self._build_extractors()
        logger.info("CommandParser initialized")
    
    def _build_patterns(self) -> Dict[IntentType, List[Dict]]:
        """Build regex patterns for intent recognition"""
        return {
            # Power Management
            IntentType.SHUTDOWN: [
                {"pattern": r"\b(shutdown|power off|turn off|shut down)\b", "weight": 1.0},
                {"pattern": r"\bshutdown in (\d+)\s*(minute|min|hour|hr)s?\b", "weight": 1.0, "entities": ["delay"]},
                {"pattern": r"\bshutdown at (\d{1,2}:\d{2})\b", "weight": 0.9, "entities": ["time"]},
            ],
            IntentType.REBOOT: [
                {"pattern": r"\b(reboot|restart)\b", "weight": 1.0},
                {"pattern": r"\breboot in (\d+)\s*(minute|min|hour|hr)s?\b", "weight": 1.0, "entities": ["delay"]},
            ],
            IntentType.SUSPEND: [
                {"pattern": r"\b(suspend|sleep|standby)\b", "weight": 1.0},
            ],
            IntentType.HIBERNATE: [
                {"pattern": r"\bhibernate\b", "weight": 1.0},
            ],
            IntentType.LOCK: [
                {"pattern": r"\b(lock|lock screen|lock computer)\b", "weight": 1.0},
            ],
            IntentType.LOGOUT: [
                {"pattern": r"\b(logout|log out|sign out)\b", "weight": 1.0},
            ],
            
            # Applications
            IntentType.OPEN_BROWSER: [
                {"pattern": r"\b(open|launch|start)\s+(browser|firefox|chrome|chromium|brave|edge)\b", "weight": 1.0},
                {"pattern": r"\b(open|go to)\s+(https?://\S+)\b", "weight": 0.9, "entities": ["url"]},
            ],
            IntentType.OPEN_TERMINAL: [
                {"pattern": r"\b(open|launch|start)\s+(terminal|console|shell)\b", "weight": 1.0},
            ],
            IntentType.OPEN_FILE_MANAGER: [
                {"pattern": r"\b(open|launch|start)\s+(files?|file manager|nautilus|dolphin|thunar)\b", "weight": 1.0},
            ],
            IntentType.OPEN_TEXT_EDITOR: [
                {"pattern": r"\b(open|launch|start)\s+(editor|text editor|gedit|notepad)\b", "weight": 1.0},
            ],
            IntentType.OPEN_CODE_EDITOR: [
                {"pattern": r"\b(open|launch|start)\s+(code|vscode|visual studio code)\b", "weight": 1.0},
            ],
            IntentType.OPEN_APPLICATION: [
                {"pattern": r"\b(open|launch|start|run)\s+(\w+)\b", "weight": 0.7, "entities": ["app_name"]},
            ],
            IntentType.CLOSE_APPLICATION: [
                {"pattern": r"\b(close|quit|exit|kill)\s+(\w+)\b", "weight": 0.9, "entities": ["app_name"]},
            ],
            
            # Files
            IntentType.CREATE_FILE: [
                {"pattern": r"\b(create|make|new)\s+file\s+(\S+)(?:\s+with\s+content\s+(.+))?\b", "weight": 1.0, "entities": ["path", "content"]},
                {"pattern": r"\bwrite\s+(.+)\s+to\s+file\s+(\S+)\b", "weight": 0.9, "entities": ["content", "path"]},
            ],
            IntentType.CREATE_DIRECTORY: [
                {"pattern": r"\b(create|make|new)\s+(folder|directory|dir)\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
            ],
            IntentType.DELETE_FILE: [
                {"pattern": r"\b(delete|remove|rm)\s+file\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
                {"pattern": r"\bdelete\s+(\S+)\b", "weight": 0.6, "entities": ["path"]},
            ],
            IntentType.DELETE_DIRECTORY: [
                {"pattern": r"\b(delete|remove|rm)\s+(folder|directory|dir)\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
                {"pattern": r"\bdelete\s+(folder|directory)\s+(\S+)\s+(force|recursive)\b", "weight": 1.0, "entities": ["path", "recursive"]},
            ],
            IntentType.COPY_FILE: [
                {"pattern": r"\bcopy\s+(\S+)\s+to\s+(\S+)\b", "weight": 1.0, "entities": ["source", "destination"]},
                {"pattern": r"\bcopy\s+(\S+)\s+(\S+)\b", "weight": 0.7, "entities": ["source", "destination"]},
            ],
            IntentType.MOVE_FILE: [
                {"pattern": r"\bmove\s+(\S+)\s+to\s+(\S+)\b", "weight": 1.0, "entities": ["source", "destination"]},
            ],
            IntentType.RENAME_FILE: [
                {"pattern": r"\brename\s+(\S+)\s+to\s+(\S+)\b", "weight": 1.0, "entities": ["path", "new_name"]},
            ],
            IntentType.LIST_DIRECTORY: [
                {"pattern": r"\b(list|show|ls)\s+(files?|directory|folder)?\s*(\S*)\b", "weight": 0.9, "entities": ["path"]},
                {"pattern": r"\bwhat('?s| is)\s+in\s+(\S+)\b", "weight": 0.8, "entities": ["path"]},
            ],
            IntentType.SEARCH_FILES: [
                {"pattern": r"\b(find|search|locate)\s+(files?\s+)?(named\s+)?(\S+)\b", "weight": 1.0, "entities": ["pattern"]},
                {"pattern": r"\b(find|search)\s+(\S+)\s+files?\b", "weight": 0.9, "entities": ["pattern"]},
            ],
            IntentType.READ_FILE: [
                {"pattern": r"\b(read|show|cat|display)\s+file\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
                {"pattern": r"\bwhat('?s| is)\s+in\s+file\s+(\S+)\b", "weight": 0.9, "entities": ["path"]},
            ],
            IntentType.WRITE_FILE: [
                {"pattern": r"\bwrite\s+(.+)\s+to\s+(\S+)\b", "weight": 0.9, "entities": ["content", "path"]},
                {"pattern": r"\bappend\s+(.+)\s+to\s+(\S+)\b", "weight": 0.9, "entities": ["content", "path", "append"]},
            ],
            IntentType.CHANGE_DIRECTORY: [
                {"pattern": r"\b(go to|cd|change (to )?(directory|folder))\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
            ],
            IntentType.GET_FILE_INFO: [
                {"pattern": r"\b(info|details|stat)\s+(?:of\s+)?file\s+(\S+)\b", "weight": 1.0, "entities": ["path"]},
            ],
            IntentType.DISK_USAGE: [
                {"pattern": r"\b(disk usage|disk space|free space)\b", "weight": 1.0},
            ],
            IntentType.FIND_LARGE_FILES: [
                {"pattern": r"\b(find|largest)\s+large\s+files?\b", "weight": 1.0},
            ],
            
            # System Settings - Brightness
            IntentType.SET_BRIGHTNESS: [
                {"pattern": r"\b(set|change)\s+brightness\s+to\s+(\d+)\b", "weight": 1.0, "entities": ["value"]},
                {"pattern": r"\bbrightness\s+(\d+)\b", "weight": 0.8, "entities": ["value"]},
            ],
            IntentType.GET_BRIGHTNESS: [
                {"pattern": r"\b(what('?s| is)|show|get)\s+brightness\b", "weight": 1.0},
            ],
            IntentType.INCREASE_BRIGHTNESS: [
                {"pattern": r"\b(increase|raise|turn up|brighter)\s+brightness\b", "weight": 1.0},
                {"pattern": r"\bbrightness\s+(up|higher)\b", "weight": 0.8},
            ],
            IntentType.DECREASE_BRIGHTNESS: [
                {"pattern": r"\b(decrease|lower|turn down|dimmer)\s+brightness\b", "weight": 1.0},
                {"pattern": r"\bbrightness\s+(down|lower)\b", "weight": 0.8},
            ],
            
            # System Settings - Volume
            IntentType.SET_VOLUME: [
                {"pattern": r"\b(set|change)\s+volume\s+to\s+(\d+)\b", "weight": 1.0, "entities": ["value"]},
                {"pattern": r"\bvolume\s+(\d+)\b", "weight": 0.8, "entities": ["value"]},
            ],
            IntentType.GET_VOLUME: [
                {"pattern": r"\b(what('?s| is)|show|get)\s+volume\b", "weight": 1.0},
            ],
            IntentType.INCREASE_VOLUME: [
                {"pattern": r"\b(increase|raise|turn up|louder)\s+volume\b", "weight": 1.0},
                {"pattern": r"\bvolume\s+(up|higher)\b", "weight": 0.8},
            ],
            IntentType.DECREASE_VOLUME: [
                {"pattern": r"\b(decrease|lower|turn down|quieter)\s+volume\b", "weight": 1.0},
                {"pattern": r"\bvolume\s+(down|lower)\b", "weight": 0.8},
            ],
            IntentType.MUTE_VOLUME: [
                {"pattern": r"\b(mute|silence)\b", "weight": 1.0},
            ],
            IntentType.UNMUTE_VOLUME: [
                {"pattern": r"\b(unmute|sound on)\b", "weight": 1.0},
            ],
            
            # System Settings - Resolution
            IntentType.SET_RESOLUTION: [
                {"pattern": r"\b(set|change)\s+resolution\s+to\s+(\d+)x(\d+)(?:@(\d+))?\b", "weight": 1.0, "entities": ["width", "height", "rate"]},
                {"pattern": r"\bresolution\s+(\d+)x(\d+)\b", "weight": 0.8, "entities": ["width", "height"]},
            ],
            IntentType.GET_RESOLUTION: [
                {"pattern": r"\b(what('?s| is)|show|get)\s+resolution\b", "weight": 1.0},
            ],
            IntentType.LIST_RESOLUTIONS: [
                {"pattern": r"\b(list|show)\s+resolutions\b", "weight": 1.0},
            ],
            
            # System Commands
            IntentType.RUN_UPDATE: [
                {"pattern": r"\b(update|upgrade)\s+(system|packages?)\b", "weight": 1.0},
                {"pattern": r"\brun\s+update\b", "weight": 1.0},
            ],
            IntentType.RUN_COMMAND: [
                {"pattern": r"\brun\s+command\s+(.+)\b", "weight": 1.0, "entities": ["command"]},
                {"pattern": r"\bexecute\s+(.+)\b", "weight": 0.8, "entities": ["command"]},
            ],
            IntentType.SHUTDOWN_TIMER: [
                {"pattern": r"\bshutdown\s+in\s+(\d+)\s*(minute|min|hour|hr)s?\b", "weight": 1.0, "entities": ["minutes"]},
            ],
            IntentType.CANCEL_SHUTDOWN: [
                {"pattern": r"\bcancel\s+shutdown\b", "weight": 1.0},
            ],
            IntentType.SHOW_UPTIME: [
                {"pattern": r"\b(uptime|how long)\b", "weight": 1.0},
            ],
            IntentType.SHOW_USERS: [
                {"pattern": r"\b(who|users|logged in)\b", "weight": 0.8},
            ],
            
            # System Monitoring
            IntentType.GET_CPU_USAGE: [
                {"pattern": r"\b(cpu|processor)\s+(usage|utilization|load)\b", "weight": 1.0},
                {"pattern": r"\bhow('?s| is)\s+(the\s+)?cpu\b", "weight": 0.9},
            ],
            IntentType.GET_MEMORY_USAGE: [
                {"pattern": r"\b(memory|ram)\s+(usage|utilization)\b", "weight": 1.0},
                {"pattern": r"\bhow('?s| is)\s+(the\s+)?(memory|ram)\b", "weight": 0.9},
            ],
            IntentType.GET_DISK_USAGE: [
                {"pattern": r"\b(disk|storage)\s+(usage|space|free)\b", "weight": 1.0},
            ],
            IntentType.GET_TEMPERATURE: [
                {"pattern": r"\b(temperature|temp|heat)\b", "weight": 1.0},
            ],
            IntentType.GET_BATTERY: [
                {"pattern": r"\b(battery|power)\b", "weight": 1.0},
            ],
            IntentType.GET_NETWORK_INFO: [
                {"pattern": r"\b(network|internet|connection)\s+(info|status|speed)\b", "weight": 1.0},
                {"pattern": r"\b(ip address|my ip)\b", "weight": 0.9},
            ],
            IntentType.GET_PROCESSES: [
                {"pattern": r"\b(top|running)\s+(processes?|programs?)\b", "weight": 1.0},
                {"pattern": r"\bwhat('?s| is)\s+running\b", "weight": 0.8},
            ],
            IntentType.SYSTEM_SUMMARY: [
                {"pattern": r"\b(system\s+)?(summary|status|report|overview)\b", "weight": 1.0},
            ],
            
            # Help
            IntentType.SHOW_HELP: [
                {"pattern": r"\bhelp\b", "weight": 1.0},
                {"pattern": r"\bhelp\s+(\w+)\b", "weight": 1.0, "entities": ["topic"]},
            ],
            IntentType.SHOW_COMMAND_HELP: [
                {"pattern": r"\bhelp\s+(?:command\s+)?(\w+)\b", "weight": 1.0, "entities": ["command"]},
            ],
            IntentType.LIST_COMMANDS: [
                {"pattern": r"\b(list|show)\s+commands\b", "weight": 1.0},
            ],
            IntentType.SHOW_TUTORIAL: [
                {"pattern": r"\btutorial\b", "weight": 1.0},
            ],
            IntentType.SEARCH_HELP: [
                {"pattern": r"\b(search|find)\s+help\s+(?:for\s+)?(\w+)\b", "weight": 1.0, "entities": ["query"]},
            ],
        }
    
    def _build_extractors(self) -> Dict[str, callable]:
        """Build entity extraction functions"""
        return {
            "value": self._extract_number,
            "delay": self._extract_time_minutes,
            "time": self._extract_time,
            "url": self._extract_url,
            "app_name": self._extract_app_name,
            "path": self._extract_path,
            "source": self._extract_path,
            "destination": self._extract_path,
            "new_name": self._extract_name,
            "pattern": self._extract_pattern,
            "content": self._extract_content,
            "command": self._extract_command,
            "minutes": self._extract_number,
            "width": self._extract_number,
            "height": self._extract_number,
            "rate": self._extract_number,
            "topic": self._extract_word,
            "query": self._extract_word,
        }
    
    def parse(self, text: str) -> ParsedCommand:
        """Parse natural language text into command"""
        text = text.lower().strip()
        
        # Remove wake word if present
        wake_words = ["assistant", "hey assistant", "okay assistant", "computer"]
        for ww in wake_words:
            if text.startswith(ww):
                text = text[len(ww):].strip()
                if text.startswith(","):
                    text = text[1:].strip()
        
        # Try each intent pattern
        best_match = None
        best_score = 0.0
        best_entities = {}
        
        for intent_type, patterns in self.patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info["pattern"]
                weight = pattern_info.get("weight", 1.0)
                entity_names = pattern_info.get("entities", [])
                
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    score = weight * 0.9  # Base score
                    
                    # Extract entities
                    entities = {}
                    for i, entity_name in enumerate(entity_names):
                        if i + 1 <= len(match.groups()):
                            value = match.group(i + 1)
                            extractor = self.entity_extractors.get(entity_name)
                            if extractor:
                                entities[entity_name] = extractor(value)
                            else:
                                entities[entity_name] = value
                    
                    # Boost score for more specific matches
                    if len(match.group(0)) > 10:
                        score += 0.1
                    
                    if score > best_score:
                        best_score = score
                        best_match = intent_type
                        best_entities = entities
        
        if best_match:
            return ParsedCommand(
                intent=best_match.value,
                entities=best_entities,
                raw_text=text,
                confidence=min(best_score, 1.0)
            )
        
        return ParsedCommand(
            intent=IntentType.UNKNOWN.value,
            entities={},
            raw_text=text,
            confidence=0.0
        )
    
    # Entity extraction methods
    def _extract_number(self, text: str) -> int:
        """Extract number from text"""
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0
    
    def _extract_time_minutes(self, text: str) -> int:
        """Extract time in minutes"""
        match = re.search(r'(\d+)', text)
        if not match:
            return 0
        value = int(match.group(1))
        if "hour" in text or "hr" in text:
            value *= 60
        return value
    
    def _extract_time(self, text: str) -> str:
        """Extract time string"""
        match = re.search(r'(\d{1,2}:\d{2})', text)
        return match.group(1) if match else ""
    
    def _extract_url(self, text: str) -> str:
        """Extract URL"""
        match = re.search(r'(https?://\S+)', text)
        return match.group(1) if match else text
    
    def _extract_app_name(self, text: str) -> str:
        """Extract application name"""
        return text.strip()
    
    def _extract_path(self, text: str) -> str:
        """Extract file path"""
        return text.strip().strip('"\'')
    
    def _extract_name(self, text: str) -> str:
        """Extract name"""
        return text.strip().strip('"\'')
    
    def _extract_pattern(self, text: str) -> str:
        """Extract search pattern"""
        return text.strip().strip('"\'')
    
    def _extract_content(self, text: str) -> str:
        """Extract content"""
        return text.strip().strip('"\'')
    
    def _extract_command(self, text: str) -> str:
        """Extract command"""
        return text.strip()
    
    def _extract_word(self, text: str) -> str:
        """Extract single word"""
        return text.strip().split()[0] if text.strip() else ""
    
    def parse_multiple(self, text: str) -> List[ParsedCommand]:
        """Parse multiple commands in one utterance"""
        # Split by conjunctions
        conjunctions = [" and ", " then ", " after that ", "; "]
        parts = [text]
        
        for conj in conjunctions:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(conj))
            parts = new_parts
        
        commands = []
        for part in parts:
            part = part.strip()
            if part:
                commands.append(self.parse(part))
        
        return commands
    
    def get_suggestions(self, partial: str, limit: int = 5) -> List[str]:
        """Get command suggestions for partial input"""
        partial = partial.lower()
        suggestions = []
        
        # Common command starters
        starters = [
            "open ", "create ", "delete ", "copy ", "move ", "rename ",
            "set ", "get ", "increase ", "decrease ", "list ", "find ",
            "read ", "write ", "run ", "show ", "help ", "shutdown ",
            "reboot ", "suspend ", "lock ", "logout "
        ]
        
        for starter in starters:
            if starter.startswith(partial) or partial.startswith(starter):
                suggestions.append(starter.strip())
        
        return suggestions[:limit]
    
    def test(self) -> bool:
        """Test command parser"""
        test_cases = [
            ("shutdown", IntentType.SHUTDOWN),
            ("shutdown in 5 minutes", IntentType.SHUTDOWN),
            ("reboot", IntentType.REBOOT),
            ("suspend", IntentType.SUSPEND),
            ("open firefox", IntentType.OPEN_BROWSER),
            ("open terminal", IntentType.OPEN_TERMINAL),
            ("create file test.txt with content hello", IntentType.CREATE_FILE),
            ("create folder projects", IntentType.CREATE_DIRECTORY),
            ("delete file test.txt", IntentType.DELETE_FILE),
            ("copy file.txt to backup.txt", IntentType.COPY_FILE),
            ("set brightness to 50", IntentType.SET_BRIGHTNESS),
            ("increase volume", IntentType.INCREASE_VOLUME),
            ("mute", IntentType.MUTE_VOLUME),
            ("cpu usage", IntentType.GET_CPU_USAGE),
            ("memory usage", IntentType.GET_MEMORY_USAGE),
            ("disk usage", IntentType.GET_DISK_USAGE),
            ("temperature", IntentType.GET_TEMPERATURE),
            ("battery", IntentType.GET_BATTERY),
            ("network info", IntentType.GET_NETWORK_INFO),
            ("top processes", IntentType.GET_PROCESSES),
            ("system summary", IntentType.SYSTEM_SUMMARY),
            ("help", IntentType.SHOW_HELP),
            ("help shutdown", IntentType.SHOW_HELP),
            ("tutorial", IntentType.SHOW_TUTORIAL),
            ("run command ls -la", IntentType.RUN_COMMAND),
            ("update system", IntentType.RUN_UPDATE),
            ("uptime", IntentType.SHOW_UPTIME),
            ("list files", IntentType.LIST_DIRECTORY),
            ("find pdf files", IntentType.SEARCH_FILES),
            ("read file notes.txt", IntentType.READ_FILE),
        ]
        
        passed = 0
        for text, expected_intent in test_cases:
            result = self.parse(text)
            if result.intent == expected_intent.value:
                passed += 1
            else:
                logger.warning(f"Parse failed: '{text}' -> {result.intent} (expected {expected_intent.value})")
        
        logger.info(f"Command parser test: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
    
    def add_pattern(self, intent: IntentType, pattern: str, weight: float = 1.0, entities: List[str] = None):
        """Add custom pattern"""
        if intent not in self.patterns:
            self.patterns[intent] = []
        self.patterns[intent].append({
            "pattern": pattern,
            "weight": weight,
            "entities": entities or []
        })
    
    def remove_pattern(self, intent: IntentType, pattern: str):
        """Remove pattern"""
        if intent in self.patterns:
            self.patterns[intent] = [
                p for p in self.patterns[intent] 
                if p["pattern"] != pattern
            ]