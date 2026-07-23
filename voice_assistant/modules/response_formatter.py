"""
Response Formatter Module
Provides structured responses with adaptive verbosity for TTS output.
Now with Gemini-style conversational responses.
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
    """Formats responses with Gemini-style conversational tone"""
    
    # Thresholds for TTS suppression (characters)
    TTS_SUPPRESS_LENGTH = 250
    
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
        
        # Auto-suppress TTS for very long responses
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
        
        # Don't transform already conversational responses (detect by checking if it has natural patterns)
        # Skip very short messages and error messages that are already conversational
        if len(msg) < 5:
            return response
        
        # Apply transformations based on response type and content
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
            # "Failed to set brightness: Permission denied" → "Hmm, I couldn't change the brightness. It looks like a permission issue."
            reason_match = re.search(r':\s*(.+)$', msg)
            action_match = re.match(r'[Ff]ailed to\s+(.+?):', msg)
            if action_match and reason_match:
                action = action_match.group(1).strip()
                reason = reason_match.group(1).strip()
                return f"Sorry, I wasn't able to {action}. {reason.capitalize()}."
            reason_match2 = re.search(r'[Ff]ailed to\s+(.+?)$', msg)
            if reason_match2:
                action = reason_match2.group(1).strip()
                return f"Sorry, I couldn't {action}. Let me know if you'd like to try something else."
            return f"Hmm, something went wrong: {msg.replace('Failed to ', '').replace('Error: ', '')}"
        
        # --- SYSTEM MONITOR RESPONSES ---
        # CPU Usage
        cpu_match = re.search(r'CPU Usage:\s*([\d.]+)%', msg)
        if cpu_match:
            pct = float(cpu_match.group(1))
            bar_clean = re.sub(r'\s*\[[█░]+\]', '', msg)
            freq_match = re.search(r'@\s*([\d.]+)MHz', msg)
            load_match = re.search(r'Load Average:\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)', msg)
            cores_match = re.search(r'Cores:\s*(\d+)\s+logical', msg)
            
            load_text = ""
            if load_match:
                l1, l5, l15 = load_match.group(1), load_match.group(2), load_match.group(3)
                load_text = f" with a load average of {l1}, {l5}, and {l15} over the last 1, 5, and 15 minutes"
            
            cores_text = ""
            if cores_match:
                cores_text = f" across {cores_match.group(1)} logical cores"
            
            freq_text = ""
            if freq_match:
                freq_text = f" running at {freq_match.group(1)} MHz"
            
            if pct < 30:
                feeling = "pretty relaxed"
            elif pct < 60:
                feeling = "moderate"
            elif pct < 85:
                feeling = "fairly busy"
            else:
                feeling = "quite high"
            
            return f"Your CPU is at {pct}%{freq_text} — that's {feeling}{load_text}{cores_text}."
        
        # Memory Usage
        mem_match = re.search(r'Memory Usage:\s*([\d.]+)%', msg)
        if mem_match:
            pct = float(mem_match.group(1))
            total_match = re.search(r'Total:\s*([\d.]+)(\w+)', msg)
            used_match = re.search(r'Used:\s*([\d.]+)(\w+)', msg)
            
            used_text = ""
            total_text = ""
            if used_match:
                used_text = f"using {used_match.group(1)}{used_match.group(2)}"
            if total_match:
                total_text = f"out of {total_match.group(1)}{total_match.group(2)}"
            
            if pct < 40:
                feeling = "plenty of room"
            elif pct < 70:
                feeling = "doing okay"
            elif pct < 85:
                feeling = "getting a bit full"
            else:
                feeling = "pretty high — you might want to close some applications"
            
            return f"Your memory is at {pct}% — {used_text} {total_text} if you want the exact numbers. That's {feeling}."
        
        # Disk Usage (single path)
        disk_single = re.search(r'Disk Usage for\s+(.+?):\s*([\d.]+)%', msg)
        if disk_single:
            path = disk_single.group(1)
            pct = float(disk_single.group(2))
            free_match = re.search(r'Free:\s*([\d.]+)(\w+)', msg)
            total_match2 = re.search(r'Total:\s*([\d.]+)(\w+)', msg)
            
            free_text = ""
            if free_match:
                free_text = f", with {free_match.group(1)}{free_match.group(2)} free"
            total_text = ""
            if total_match2:
                total_text = f"out of {total_match2.group(1)}{total_match2.group(2)}"
            
            if pct < 50:
                feeling = "still plenty of space left"
            elif pct < 80:
                feeling = "filling up but still okay"
            elif pct < 90:
                feeling = "getting quite full"
            else:
                feeling = "almost full — you might want to free up some space"
            
            return f"Your storage at {path} is {pct}% used{free_text} {total_text}. That means {feeling}."
        
        # Disk Usage (multiple partitions)
        if msg.strip().startswith("Disk Usage:") and not disk_single:
            lines = msg.strip().split('\n')
            partitions = []
            for line in lines:
                pct_m = re.search(r'([\d.]+)%', line)
                # Match any device path or mount point
                dev_m = re.search(r'(\S+)\s+\(', line)
                if pct_m and dev_m:
                    dev = dev_m.group(1)
                    pct = pct_m.group(1)
                    partitions.append(f"{dev} at {pct}%")
            if partitions:
                parts_text = "; ".join(partitions)
                return f"Here's your disk usage: {parts_text}. Let me know if you want details on any specific drive."
        
        # Temperature
        temp_match = re.search(r'System Temperatures:', msg)
        if temp_match:
            temps = re.findall(r'([\w\s-]+):\s*([\d.]+)°C', msg)
            if temps:
                temp_parts = []
                for name, val in temps:
                    name = name.strip()
                    temp_parts.append(f"{name} at {val}°C")
                temp_text = ", ".join(temp_parts)
                
                # Check if any temps are high
                high_temps = [t for t in temps if float(t[1]) > 80]
                if high_temps:
                    warning = " Some components are running quite hot!"
                else:
                    warning = " Everything looks within normal range."
                
                return f"Here are your system temperatures: {temp_text}.{warning}"
        
        # Battery
        batt_match = re.search(r'Battery:\s*([\d.]+)%', msg)
        if batt_match:
            pct = float(batt_match.group(1))
            status_match = re.search(r'\((Charging|Discharging)\)', msg)
            time_match = re.search(r'Time remaining:\s*(.+?)(?:\n|$)', msg)
            
            status = ""
            if status_match:
                s = status_match.group(1)
                status = " and it's currently charging" if "Charge" in s else " and it's discharging"
            
            time_text = ""
            if time_match:
                t = time_match.group(1).strip()
                time_text = f" with about {t.lower()} left"
            
            plugged = "plugged in" if "Charging" in status else "on battery"
            
            if pct < 15:
                return f"Your battery is at {pct}%{time_text}. You might want to plug in soon!"
            elif pct < 30:
                return f"Your battery's at {pct}%{time_text} — still okay but keep an eye on it."
            elif pct < 70:
                return f"Battery is at {pct}%{status}{time_text}. Looking good!"
            else:
                return f"Your battery is at {pct}%{status}{time_text} — plenty of charge left!"
        
        # Network Info
        net_match = re.search(r'Network Interface:\s*(\S+)', msg)
        if net_match:
            interface = net_match.group(1)
            ip_match = re.search(r'IPv4:\s*(\S+)', msg)
            status_match = re.search(r'Status:\s*(Up|Down)', msg)
            
            ip_text = ""
            if ip_match:
                ip_text = f" with IP address {ip_match.group(1)}"
            status_text = ""
            if status_match:
                status_text = f" It's currently {status_match.group(1).lower()}."
            
            return f"Your {interface} interface{ip_text}.{status_text}"
        
        # Top Processes
        proc_match = re.search(r'Top\s+(\d+)\s+processes', msg)
        if proc_match:
            count = int(proc_match.group(1))
            lines = msg.strip().split('\n')
            proc_list = []
            for line in lines[3:]:  # Skip header (lines 0-2: title, column headers, dashes)
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    name = parts[-1]
                    cpu = parts[-4]
                    mem = parts[-3]
                    proc_list.append(f"{name} at {cpu}% CPU and {mem}% memory")
            
            if proc_list:
                top_text = ", ".join(proc_list[:count])
                return f"Here are the top {count} processes: {top_text}."
        
        # File created (from files.py)
        if msg.startswith("File created:"):
            path = msg[len("File created:"):].strip()
            name = path.split("/")[-1] if "/" in path else path
            return f"All set! Created '{name}'."
        if msg.startswith("Directory created:"):
            path = msg[len("Directory created:"):].strip()
            name = path.split("/")[-1] if "/" in path else path
            return f"Done! Created a new folder called '{name}'."
        if "File deleted:" in msg or "Directory deleted:" in msg:
            name_match = re.search(r'(?:File|Directory) deleted:\s*(.+)$', msg)
            if name_match:
                return f"Deleted {name_match.group(1).strip()}. It's gone!"
        
        # Temperature (non-system format)
        temp_match_gen = re.search(r'(CPU|GPU|Core)\s+at\s+([\d.]+)°C', msg)
        if temp_match_gen and "Temperature" in msg:
            all_temps = re.findall(r'(\w+)\s+at\s+([\d.]+)°C', msg)
            if all_temps:
                temp_str = ", ".join([f"{t[0]} at {t[1]}°C" for t in all_temps])
                return f"Here are the temperatures: {temp_str}. Everything looks normal."
        
        # Application not found
        not_found = re.search(r'[Aa]pplication not found:\s*(\S+?)(?:\.|\s|$)', msg)
        if not_found:
            app = not_found.group(1).strip().rstrip(".")
            return f"Sorry, I couldn't find an application called '{app}'. You might want to check the name and try again."
        
        # Permission denied (generic)
        if "permission denied" in msg.lower() and msg.lower().startswith(("failed", "error", "permission")):
            return "Sorry, I don't have the right permissions for that. You might need to run this with sudo privileges."
        
        # System Summary
        if "SYSTEM SUMMARY" in msg.upper() and "Hostname:" in msg:
            host_match = re.search(r'Hostname:\s*(\S+)', msg)
            cpu_m = re.search(r'CPU Usage:\s*([\d.]+)%', msg)
            mem_m = re.search(r'Memory Usage:\s*([\d.]+)%', msg)
            
            host = host_match.group(1) if host_match else "your system"
            cpu_t = f"CPU at {cpu_m.group(1)}%" if cpu_m else ""
            mem_t = f"memory at {mem_m.group(1)}%" if mem_m else ""
            
            stats = ", ".join(filter(None, [cpu_t, mem_t]))
            return f"Here's a quick look at {host}: {stats}. I can go deeper on any specific area if you'd like."
        
        # --- ACTION RESULTS ---
        # Volume/Brightness settings
        vol_set = re.search(r'Volume set to\s*(\d+)%', msg)
        if vol_set:
            return f"Done! I've set the volume to {vol_set.group(1)}%."
        
        bri_set = re.search(r'Brightness set to\s*(\d+)%', msg)
        if bri_set:
            return f"Sure! Screen brightness is now at {bri_set.group(1)}%."
        
        # Volume/Brightness gets
        vol_get = re.search(r'Current volume:\s*(\d+)%', msg)
        if vol_get:
            return f"Your volume is currently at {vol_get.group(1)}%."
        
        bri_get = re.search(r'Current brightness:\s*(\d+)%', msg)
        if bri_get:
            return f"Your screen brightness is at {bri_get.group(1)}% right now."
        
        # Mute/Unmute
        if re.match(r'Volume muted', msg):
            return "Done! Audio is now muted."
        if re.match(r'Volume unmuted', msg):
            return "Done! Audio is back on."
        if msg.lower().strip() == "volume is not muted" or msg.lower().strip() == "volume is not mute":
            return "Your audio is not muted — it's on."
        if msg.lower().strip() == "volume is muted" or msg.lower().strip() == "volume is mute":
            return "Your audio is currently muted."
        
        # Resolution
        res_set = re.search(r'Resolution set to\s*(\d+x\d+)', msg)
        if res_set:
            return f"Changed! Resolution is now {res_set.group(1)}."
        res_get = re.search(r'Current resolution:\s*(\S+)', msg)
        if res_get:
            return f"You're currently running at {res_get.group(1)}."
        
        # File operations
        file_create = re.search(r'Created file:\s*(.+)', msg) or re.search(r'Created (?:file|directory):\s*(.+)', msg)
        if file_create:
            return f"All set! Created {file_create.group(1).strip()}."
        if msg.strip().startswith("Created"):
            return f"Done! {msg.strip()}"
        
        file_del = re.search(r'Deleted\s+(.+)$', msg)
        if file_del:
            return f"Deleted {file_del.group(1).strip()}. It's gone!"
        
        file_copy = re.search(r'Copied\s+(.+?)\s+to\s+(.+?)$', msg)
        if file_copy:
            return f"Copied {file_copy.group(1).strip()} to {file_copy.group(2).strip()}."
        
        file_move = re.search(r'Moved\s+(.+?)\s+to\s+(.+?)$', msg)
        if file_move:
            return f"Moved {file_move.group(1).strip()} to {file_move.group(2).strip()}."
        
        file_read = re.search(r'Read file:\s*(.+)', msg) or re.search(r'Contents of\s+(.+)', msg)
        if file_read:
            return msg  # File content is content, leave it
        
        # Application operations
        app_open = re.search(r'(?:Opening|Open|Launched|Started)\s+(.+)', msg)
        if app_open:
            name = app_open.group(1).strip().rstrip(".")
            return f"Opening {name} now!"
        app_close = re.search(r'(?:Close|Closed|Quit|Killed)[:\s]+(.+)', msg)
        if app_close:
            name = app_close.group(1).strip().rstrip(".")
            return f"Closed {name}."
        
        # Power operations
        if "shutdown" in msg.lower() and "scheduled" in msg.lower():
            time_m = re.search(r'(\d+)\s*(minute|min|hour|hr)s?', msg)
            if time_m:
                unit = {"minute": "minute", "min": "minute", "hour": "hour", "hr": "hour"}.get(time_m.group(2), "minute")
                num = int(time_m.group(1))
                plural = "s" if num != 1 else ""
                return f"Got it! I'll shut down the system in {num} {unit}{plural}."
            return "Shutdown has been scheduled."
        if re.match(r'System will shutdown', msg):
            time_m = re.search(r'(\d+)\s*(minute|min|hour|hr)s?', msg)
            if time_m:
                unit = {"minute": "minute", "min": "minute", "hour": "hour", "hr": "hour"}.get(time_m.group(2), "minute")
                num = int(time_m.group(1))
                plural = "s" if num != 1 else ""
                return f"Got it! I'll shut down the system in {num} {unit}{plural}."
        if msg.lower().startswith("cancel") or msg.lower().startswith("shutdown cancelled") or msg.lower().startswith("reboot cancelled"):
            return "Alright, I've cancelled that."
        
        # Run command
        cmd_run = re.search(r'Command output:\s*(.*)', msg, re.DOTALL)
        if cmd_run:
            output = cmd_run.group(1).strip()[:100]
            return f"Here's what I got: {output}"
        
        # System update
        if "update" in msg.lower() and ("success" in msg.lower() or "complete" in msg.lower() or "done" in msg.lower()):
            return "System update completed successfully! Everything should be up to date now."
        # Generic "system update" messages
        if "update" in msg.lower() and ("system" in msg.lower() or "package" in msg.lower()):
            return msg
        
        # Uptime
        uptime_match = re.search(r'Uptime:\s*(.+)', msg) or re.search(r'(?:System )?[Uu]ptime[:\s]*(.+)', msg)
        if uptime_match:
            return f"Your system has been running for {uptime_match.group(1).strip()}."
        
        # Users
        if "logged in" in msg.lower():
            users = re.findall(r'(\w+)\s+[\w/:_-]+\s+[\w/:_-]+', msg)
            if users:
                user_list = ", ".join(set(users))
                return f"The following users are logged in: {user_list}."
        
        # --- GENERIC ---
        # Generic "Done."
        if msg.strip() in ("Done.", "Done"):
            return "Done! What else can I help with?"
        
        # Generic success messages
        if msg.strip().lower().startswith("success"):
            rest = re.sub(r'^[Ss]uccess(?:fully)?[:\s]*', '', msg).strip()
            if rest:
                return f"All done! {rest.capitalize()}."
            return "All done!"
        
        # Return original if no transformation matched
        return original
    
    @staticmethod
    def _make_brief(response: StructuredResponse) -> StructuredResponse:
        """Trim response to brief version"""
        if len(response.message) <= 80:
            return response
        # For brief mode on already-conversational text, just take first sentence
        first_sentence = ResponseFormatter._first_sentence(response.message)
        if len(first_sentence) > 10:
            return StructuredResponse(
                type=response.type,
                message=first_sentence,
                spoken=first_sentence,
                data=response.data,
                suggestions=response.suggestions,
                success=response.success,
                error_code=response.error_code,
                error_details=response.error_details,
                requires_confirmation=response.requires_confirmation,
                tts_suppressed=False
            )
        return response
    
    @staticmethod
    def _make_normal(response: StructuredResponse) -> StructuredResponse:
        """Ensure response is at normal verbosity"""
        if len(response.message) <= 250:
            return response
        # Truncate at sentence boundary
        truncated = response.message[:250]
        last_period = truncated.rfind('.')
        if last_period > 50:
            truncated = truncated[:last_period + 1]
        else:
            truncated += ".."
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
        return text[:80] + ".."
    
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
