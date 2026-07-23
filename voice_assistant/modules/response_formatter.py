"""
Response Formatter Module
Provides structured responses with adaptive verbosity for TTS output.
Now with Gemini-style conversational responses — short, natural, 1-2 sentences.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
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
    """Formats responses with Gemini-style conversational tone — short & natural"""
    
    # Gemini keeps TTS short — 120 chars max for spoken responses
    TTS_SUPPRESS_LENGTH = 120
    
    @staticmethod
    def format(response: StructuredResponse, verbosity: Verbosity = Verbosity.NORMAL) -> StructuredResponse:
        """Apply verbosity formatting and conversational style to a response"""
        # First, apply conversational transformation
        response = ResponseFormatter.conversationalize(response)
        
        # Then apply verbosity
        if verbosity == Verbosity.BRIEF:
            response = ResponseFormatter._make_brief(response)
        elif verbosity == Verbosity.NORMAL:
            response = ResponseFormatter._make_normal(response)
        
        # Auto-suppress TTS for long responses (Gemini keeps it < 120 chars)
        if len(response.message) > ResponseFormatter.TTS_SUPPRESS_LENGTH:
            response.tts_suppressed = True
            if not response.spoken or response.spoken == response.message:
                response.spoken = ResponseFormatter._summarize_for_tts(response)
        
        return response
    
    @staticmethod
    def conversationalize(response: StructuredResponse) -> StructuredResponse:
        """Transform a technical/robotic response into a Gemini-style conversational one"""
        if response.type in (ResponseType.HELP, ResponseType.CONFIRMATION, ResponseType.DESTRUCTIVE):
            return response  # Leave help and confirmations as-is
        
        msg = response.message
        if len(msg) < 5:
            return response
        
        conversational = ResponseFormatter._transform_message(msg, response.type)
        
        if conversational != msg:
            response = StructuredResponse(
                type=response.type,
                message=conversational,
                spoken=conversational,
                data=response.data,
                suggestions=response.suggestions,
                success=response.success,
                error_code=response.error_code,
                error_details=response.error_details,
                requires_confirmation=response.requires_confirmation,
                tts_suppressed=response.tts_suppressed
            )
        
        return response
    
    @staticmethod
    def _transform_message(msg: str, rtype: ResponseType) -> str:
        """Apply natural language transformations to raw technical messages"""
        original = msg
        
        # --- ERROR MESSAGES ---
        if msg.lower().startswith("failed") or msg.lower().startswith("error"):
            reason_match = re.search(r':\s*(.+)$', msg)
            action_match = re.match(r'[Ff]ailed to\s+(.+?):', msg)
            if action_match and reason_match:
                action = action_match.group(1).strip()
                reason = reason_match.group(1).strip()
                return f"Sorry, I wasn't able to {action}. {reason.capitalize()}."
            reason_match2 = re.search(r'[Ff]ailed to\s+(.+?)$', msg)
            if reason_match2:
                action = reason_match2.group(1).strip()
                return f"Sorry, I couldn't {action}."
            return f"Hmm, something went wrong: {msg.replace('Failed to ', '').replace('Error: ', '')}"
        
        # --- SYSTEM MONITOR RESPONSES (SHORT & NATURAL) ---
        # CPU Usage
        cpu_match = re.search(r'CPU Usage:\s*([\d.]+)%', msg)
        if cpu_match:
            pct = float(cpu_match.group(1))
            if pct < 30:
                return f"Your CPU is at {pct}% — pretty relaxed right now."
            elif pct < 60:
                return f"CPU is at {pct}% — doing fine."
            elif pct < 85:
                return f"CPU at {pct}% — it's a bit busy."
            else:
                return f"CPU is at {pct}% — that's quite high."
        
        # Memory Usage
        mem_match = re.search(r'Memory Usage:\s*([\d.]+)%', msg)
        if mem_match:
            pct = float(mem_match.group(1))
            used_match = re.search(r'Used:\s*([\d.]+)(\w+)', msg)
            used_text = f" ({used_match.group(1)}{used_match.group(2)} used)" if used_match else ""
            if pct < 40:
                return f"Memory at {pct}%{used_text} — plenty of room."
            elif pct < 70:
                return f"Memory at {pct}%{used_text} — still comfortable."
            elif pct < 85:
                return f"Memory at {pct}%{used_text} — getting a bit full."
            else:
                return f"Memory at {pct}%{used_text} — you may want to close some apps."
        
        # Disk Usage (single path)
        disk_single = re.search(r'Disk Usage for\s+(.+?):\s*([\d.]+)%', msg)
        if disk_single:
            pct = float(disk_single.group(2))
            path = disk_single.group(1)
            if pct < 50:
                return f"Storage at {path} is {pct}% used — plenty of space."
            elif pct < 80:
                return f"Storage at {path} is {pct}% used — still okay."
            elif pct < 90:
                return f"Storage at {path} is {pct}% used — getting full."
            else:
                return f"Storage at {path} is {pct}% used — you should free up some space."
        
        # Battery
        batt_match = re.search(r'Battery:\s*([\d.]+)%', msg)
        if batt_match:
            pct = float(batt_match.group(1))
            status_match = re.search(r'\((Charging|Discharging)\)', msg)
            time_match = re.search(r'Time remaining:\s*(.+?)(?:\n|$)', msg)
            time_text = f" ({time_match.group(1).strip()} left)" if time_match else ""
            
            if pct < 15:
                return f"Battery at {pct}%{time_text}. You should plug in soon!"
            elif pct < 30:
                return f"Battery at {pct}%{time_text} — still okay."
            elif pct < 70:
                return f"Battery at {pct}%{time_text} — looking good."
            else:
                return f"Battery at {pct}%{time_text} — plenty of charge."
        
        # Temperature
        if 'Temperature' in msg or 'temperature' in msg:
            temps = re.findall(r'([\w\s-]+):\s*([\d.]+)°C', msg)
            if temps:
                high = any(float(t[1]) > 80 for t in temps)
                if high:
                    return "Some components are running hot, but still within safe limits."
                return "All temperatures look normal."
            return msg
        
        # Network Info
        net_match = re.search(r'Network Interface:\s*(\S+)', msg)
        if net_match:
            interface = net_match.group(1)
            ip_match = re.search(r'IPv4:\s*(\S+)', msg)
            ip_text = f" at {ip_match.group(1)}" if ip_match else ""
            return f"Your {interface} interface{ip_text} is up and running."
        
        # --- ACTION RESULTS ---
        vol_set = re.search(r'Volume set to\s*(\d+)%', msg)
        if vol_set: return f"Volume at {vol_set.group(1)}% now."
        bri_set = re.search(r'Brightness set to\s*(\d+)%', msg)
        if bri_set: return f"Brightness at {bri_set.group(1)}% now."
        vol_get = re.search(r'Current volume:\s*(\d+)%', msg)
        if vol_get: return f"Volume is at {vol_get.group(1)}%."
        bri_get = re.search(r'Current brightness:\s*(\d+)%', msg)
        if bri_get: return f"Brightness is at {bri_get.group(1)}%."
        
        if re.match(r'Volume muted', msg): return "Muted."
        if re.match(r'Volume unmuted', msg): return "Unmuted."
        if msg.lower().strip() == "volume is not muted": return "Audio is on."
        if msg.lower().strip() == "volume is muted": return "Audio is muted."
        
        res_set = re.search(r'Resolution set to\s*(\S+)', msg)
        if res_set: return f"Resolution is now {res_set.group(1)}."
        res_get = re.search(r'Current resolution:\s*(\S+)', msg)
        if res_get: return f"Running at {res_get.group(1)}."
        
        app_open = re.search(r'(?:Opening|Open|Launched|Started)\s+(.+)', msg)
        if app_open: return f"Opening {app_open.group(1).strip().rstrip('.')}."
        app_close = re.search(r'(?:Close|Closed|Quit|Killed)[:\s]+(.+)', msg)
        if app_close: return f"Closed {app_close.group(1).strip().rstrip('.')}."
        
        if re.search(r'(?:File|Directory) deleted:', msg):
            name_match = re.search(r'(?:File|Directory) deleted:\s*(.+?)$', msg)
            if name_match: return f"Deleted {name_match.group(1).strip()}."
        if msg.startswith("File created:"):
            name = msg.split("/")[-1].strip() if "/" in msg else msg.replace("File created:", "").strip()
            return f"Created {name}."
        if msg.startswith("Directory created:"):
            name = msg.split("/")[-1].strip() if "/" in msg else msg.replace("Directory created:", "").strip()
            return f"Created folder {name}."
        
        if msg.strip() in ("Done.", "Done"): return "Done!"
        
        not_found = re.search(r'[Aa]pplication not found:\s*(\S+?)(?:\.|\s|$)', msg)
        if not_found: return f"Couldn't find '{not_found.group(1).strip().rstrip('.')}'."
        if "permission denied" in msg.lower():
            return "Sorry, I don't have the right permissions for that."
        
        if re.search(r'System will shutdown', msg):
            time_m = re.search(r'(\d+)\s*(minute|min|hour|hr)s?', msg)
            if time_m:
                num = int(time_m.group(1))
                unit = {"minute": "minute", "min": "minute", "hour": "hour", "hr": "hour"}.get(time_m.group(2), "minute")
                plural = "s" if num != 1 else ""
                return f"Shutting down in {num} {unit}{plural}."
        if msg.lower().startswith("shutdown cancelled") or msg.lower().startswith("reboot cancelled") or msg.lower().startswith("cancel"):
            return "Cancelled."
        
        # System update
        if ("update" in msg.lower() or "upgrade" in msg.lower()) and any(w in msg.lower() for w in ["success", "complete", "done"]):
            return "Update complete."
        
        # Generic success
        if "success" in msg.lower():
            return "All done!"
        
        return original
    
    @staticmethod
    def _make_brief(response: StructuredResponse) -> StructuredResponse:
        if len(response.message) <= 80:
            return response
        first_sentence = ResponseFormatter._first_sentence(response.message)
        if len(first_sentence) > 10:
            return StructuredResponse(type=response.type, message=first_sentence, spoken=first_sentence, data=response.data, suggestions=response.suggestions, success=response.success, error_code=response.error_code, error_details=response.error_details, requires_confirmation=response.requires_confirmation, tts_suppressed=False)
        return response
    
    @staticmethod
    def _make_normal(response: StructuredResponse) -> StructuredResponse:
        if len(response.message) <= 120:
            return response
        truncated = response.message[:120]
        last_period = truncated.rfind('.')
        if last_period > 30:
            truncated = truncated[:last_period + 1]
        else:
            truncated += ".."
        return StructuredResponse(type=response.type, message=truncated, spoken=truncated, data=response.data, suggestions=response.suggestions, success=response.success, error_code=response.error_code, error_details=response.error_details, requires_confirmation=response.requires_confirmation, tts_suppressed=False)
    
    @staticmethod
    def _summarize_for_tts(response: StructuredResponse) -> str:
        sentences = response.message.replace('!', '.').replace('?', '.').split('.')
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 10]
        if meaningful:
            return '. '.join(meaningful[:1]) + '.'  # Just one sentence
        return response.message[:80] + "."
    
    @staticmethod
    def _first_sentence(text: str) -> str:
        for delim in ['. ', '! ', '? ', '\n']:
            idx = text.find(delim)
            if idx > 0:
                return text[:idx + 1] if delim in ['. ', '! ', '? '] else text[:idx]
        return text[:80] + "."
    
    @staticmethod
    def success(message: str, **kwargs) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.ACTION_RESULT, message=message, success=True, **kwargs)
    
    @staticmethod
    def error(message: str, error_code: str = "UNKNOWN_ERROR", details: str = "", **kwargs) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.ERROR, message=message, success=False, error_code=error_code, error_details=details, **kwargs)
    
    @staticmethod
    def status(message: str, data: Any = None, **kwargs) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.STATUS, message=message, data=data, **kwargs)
    
    @staticmethod
    def destructive(message: str, **kwargs) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.DESTRUCTIVE, message=message, requires_confirmation=True, **kwargs)
    
    @staticmethod
    def info(message: str, data: Any = None, **kwargs) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.INFORMATION, message=message, data=data, **kwargs)
    
    @staticmethod
    def confirmation(question: str, action: str) -> StructuredResponse:
        return StructuredResponse(type=ResponseType.CONFIRMATION, message=question, spoken=question, requires_confirmation=True, data={"action": action}, suggestions=["yes", "no", "cancel"])


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
        destructive_intents = ["shutdown", "reboot", "suspend", "hibernate", "logout", "delete_file", "delete_directory"]
        return intent in destructive_intents
