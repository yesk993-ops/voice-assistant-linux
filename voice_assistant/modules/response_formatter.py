"""
Response Formatter Module
Provides structured responses with adaptive verbosity for TTS output.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class Verbosity(Enum):
    """Answer length levels"""
    BRIEF = "brief"        # Short, spoken once (e.g., "CPU at 23%")
    NORMAL = "normal"      # Moderate detail, spoken once
    DETAILED = "detailed"  # Full detail, may be truncated for TTS


class ResponseType(Enum):
    """Type of response for formatting decisions"""
    STATUS = "status"                 # Quick status reading (brief)
    ACTION_RESULT = "action_result"   # Command executed successfully
    ERROR = "error"                   # Something went wrong
    CONFIRMATION = "confirmation"     # Asking user to confirm
    DESTRUCTIVE = "destructive"       # Destructive action warning
    INFORMATION = "information"       # Detailed information reply
    HELP = "help"                     # Help text
    SYSTEM_INFO = "system_info"       # System information report


@dataclass
class StructuredResponse:
    """Unified response structure returned by all modules"""
    type: ResponseType
    message: str                    # Human-readable message (primary output)
    spoken: str = ""                # TTS-optimized version (auto-generated if empty)
    data: Any = None                # Raw data for display/logging
    suggestions: List[str] = field(default_factory=list)  # Follow-up suggestions
    success: bool = True
    error_code: Optional[str] = None
    error_details: Optional[str] = None
    requires_confirmation: bool = False
    tts_suppressed: bool = False    # If True, don't speak full response

    def __post_init__(self):
        if not self.spoken:
            self.spoken = self.message


class ResponseFormatter:
    """Formats responses with appropriate verbosity for TTS"""
    
    # Thresholds for TTS suppression (characters)
    TTS_SUPPRESS_LENGTH = 200
    BRIEF_MAX_LENGTH = 80
    NORMAL_MAX_LENGTH = 250
    
    @staticmethod
    def format(response: StructuredResponse, verbosity: Verbosity = Verbosity.NORMAL) -> StructuredResponse:
        """Apply verbosity formatting to a response"""
        if verbosity == Verbosity.BRIEF:
            response = ResponseFormatter._make_brief(response)
        elif verbosity == Verbosity.NORMAL:
            response = ResponseFormatter._make_normal(response)
        
        # Auto-suppress TTS for very long responses
        if len(response.message) > ResponseFormatter.TTS_SUPPRESS_LENGTH:
            response.tts_suppressed = True
            if not response.spoken or response.spoken == response.message:
                response.spoken = ResponseFormatter._summarize_for_tts(response)
        
        return response
    
    @staticmethod
    def _make_brief(response: StructuredResponse) -> StructuredResponse:
        """Trim response to brief version"""
        if len(response.message) <= ResponseFormatter.BRIEF_MAX_LENGTH:
            return response
        
        brief_messages = {
            ResponseType.STATUS: lambda r: r.message.split('.')[0] + '.' if '.' in r.message else r.message[:80],
            ResponseType.ACTION_RESULT: lambda r: "Done." if r.success else "Failed.",
            ResponseType.ERROR: lambda r: r.message.split('.')[0] + '.' if '.' in r.message else r.message[:80],
            ResponseType.SYSTEM_INFO: lambda r: ResponseFormatter._first_sentence(r.message),
            ResponseType.INFORMATION: lambda r: ResponseFormatter._first_sentence(r.message),
        }
        
        if response.type in brief_messages:
            brief = brief_messages[response.type](response)
        else:
            brief = response.message[:ResponseFormatter.BRIEF_MAX_LENGTH] + "..."
        
        return StructuredResponse(
            type=response.type,
            message=brief,
            spoken=brief,
            data=response.data,
            suggestions=response.suggestions,
            success=response.success,
            error_code=response.error_code,
            error_details=response.error_details,
            requires_confirmation=response.requires_confirmation,
            tts_suppressed=False
        )
    
    @staticmethod
    def _make_normal(response: StructuredResponse) -> StructuredResponse:
        """Ensure response is at normal verbosity"""
        if len(response.message) <= ResponseFormatter.NORMAL_MAX_LENGTH:
            return response
        
        truncated = response.message[:ResponseFormatter.NORMAL_MAX_LENGTH]
        last_period = truncated.rfind('.')
        if last_period > 50:
            truncated = truncated[:last_period + 1]
        else:
            truncated += "..."
        
        return StructuredResponse(
            type=response.type,
            message=truncated,
            spoken=truncated,
            data=response.data,
            suggestions=response.suggestions,
            success=response.success,
            error_code=response.error_code,
            error_details=response.error_details,
            requires_confirmation=response.requires_confirmation,
            tts_suppressed=False
        )
    
    @staticmethod
    def _summarize_for_tts(response: StructuredResponse) -> str:
        """Create a short TTS-friendly summary of a long response"""
        if response.data and isinstance(response.data, dict):
            parts = []
            for key, value in response.data.items():
                if isinstance(value, (int, float, str)) and len(str(value)) < 20:
                    parts.append(f"{key}: {value}")
            if parts:
                return ". ".join(parts[:3]) + "."
        
        sentences = response.message.replace('!', '.').replace('?', '.').split('.')
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 10]
        if meaningful:
            return '. '.join(meaningful[:2]) + '.'
        
        return response.message[:100] + "..."
    
    @staticmethod
    def _first_sentence(text: str) -> str:
        """Extract the first sentence from text"""
        for delim in ['. ', '! ', '? ', '\n']:
            idx = text.find(delim)
            if idx > 0:
                return text[:idx + 1] if delim in ['. ', '! ', '? '] else text[:idx]
        return text[:80] + "..."
    
    @staticmethod
    def success(message: str, **kwargs) -> StructuredResponse:
        """Create a success response"""
        return StructuredResponse(type=ResponseType.ACTION_RESULT, message=message, success=True, **kwargs)
    
    @staticmethod
    def error(message: str, error_code: str = "UNKNOWN_ERROR", details: str = "", **kwargs) -> StructuredResponse:
        """Create an error response"""
        return StructuredResponse(
            type=ResponseType.ERROR,
            message=message,
            success=False,
            error_code=error_code,
            error_details=details,
            **kwargs
        )
    
    @staticmethod
    def status(message: str, data: Any = None, **kwargs) -> StructuredResponse:
        """Create a status response"""
        return StructuredResponse(type=ResponseType.STATUS, message=message, data=data, **kwargs)
    
    @staticmethod
    def destructive(message: str, **kwargs) -> StructuredResponse:
        """Create a destructive action warning"""
        return StructuredResponse(
            type=ResponseType.DESTRUCTIVE,
            message=message,
            requires_confirmation=True,
            **kwargs
        )
    
    @staticmethod
    def info(message: str, data: Any = None, **kwargs) -> StructuredResponse:
        """Create an informational response"""
        return StructuredResponse(type=ResponseType.INFORMATION, message=message, data=data, **kwargs)
    
    @staticmethod
    def confirmation(question: str, action: str) -> StructuredResponse:
        """Create a confirmation request"""
        return StructuredResponse(
            type=ResponseType.CONFIRMATION,
            message=question,
            spoken=question,
            requires_confirmation=True,
            data={"action": action},
            suggestions=["yes", "no", "cancel"],
        )


class QueryClassifier:
    """Classifies user queries to determine response style and safety requirements"""
    
    DESTRUCTIVE_KEYWORDS = [
        "shutdown", "reboot", "restart", "suspend", "hibernate",
        "delete", "remove", "rm", "kill", "force",
        "format", "erase", "wipe", "destroy",
        "logout", "sign out",
    ]
    
    STATUS_PATTERNS = [
        "cpu usage", "memory usage", "ram usage", "disk usage",
        "temperature", "battery", "network info", "ip address",
        "how is", "what is the", "show me", "get",
        "uptime", "who is logged", "running",
    ]
    
    @staticmethod
    def classify(intent: str, text: str = "") -> ResponseType:
        """Classify a command intent into response type"""
        text_lower = text.lower()
        
        if "help" in intent.lower() or "tutorial" in intent.lower():
            return ResponseType.HELP
            
        if any(kw in intent.lower() for kw in ["shutdown", "reboot", "suspend", "hibernate", "logout"]):
            return ResponseType.DESTRUCTIVE
        if any(kw in intent.lower() for kw in ["delete_file", "delete_directory", "remove"]):
            return ResponseType.DESTRUCTIVE
        
        if any(kw in intent.lower() for kw in ["get_", "show_", "list_"]):
            return ResponseType.STATUS
        if any(kw in text_lower for kw in QueryClassifier.STATUS_PATTERNS):
            return ResponseType.STATUS
        
        if any(kw in intent.lower() for kw in ["summary", "system_summary"]):
            return ResponseType.SYSTEM_INFO
        
        if any(kw in intent.lower() for kw in ["create_", "copy_", "move_", "write_", "rename_"]):
            return ResponseType.ACTION_RESULT
        
        return ResponseType.INFORMATION
    
    @staticmethod
    def verbosity_for(intent: str, text: str = "") -> Verbosity:
        """Determine appropriate verbosity level"""
        text_lower = text.lower()
        
        if any(kw in intent.lower() for kw in ["get_", "show_", "list_"]):
            return Verbosity.BRIEF
        if any(kw in text_lower for kw in QueryClassifier.STATUS_PATTERNS):
            return Verbosity.BRIEF
        
        if "help" in intent.lower():
            return Verbosity.NORMAL
        
        if any(kw in intent.lower() for kw in ["shutdown", "reboot", "delete", "remove"]):
            return Verbosity.NORMAL
        
        if any(kw in text_lower for kw in ["explain", "describe", "tell me about", "what is"]):
            return Verbosity.DETAILED
        
        return Verbosity.NORMAL
    
    @staticmethod
    def requires_confirmation(intent: str) -> bool:
        """Check if a command requires user confirmation"""
        destructive_intents = [
            "shutdown", "reboot", "suspend", "hibernate", "logout",
            "delete_file", "delete_directory",
        ]
        return intent in destructive_intents
