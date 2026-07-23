"""
Application Launcher Module
Handles launching and managing applications
"""

import os
import logging
import subprocess
import shutil
from typing import Dict, List, Optional, Any
import psutil

logger = logging.getLogger(__name__)


class ApplicationLauncher:
    """Launches and manages applications"""
    
    def __init__(self):
        # Default commands from environment or fallbacks
        self.commands = {
            "browser": os.getenv("BROWSER_COMMAND", "firefox"),
            "terminal": os.getenv("TERMINAL_COMMAND", "gnome-terminal"),
            "file_manager": os.getenv("FILE_MANAGER_COMMAND", "nautilus"),
            "text_editor": os.getenv("TEXT_EDITOR_COMMAND", "gedit"),
            "code_editor": os.getenv("CODE_EDITOR_COMMAND", "code"),
        }
        
        # Common application mappings
        self.app_map = {
            # Browsers
            "firefox": "firefox",
            "chrome": "google-chrome",
            "chromium": "chromium-browser",
            "brave": "brave-browser",
            "edge": "microsoft-edge",
            
            # Terminals
            "terminal": "gnome-terminal",
            "konsole": "konsole",
            "xterm": "xterm",
            "alacritty": "alacritty",
            "kitty": "kitty",
            
            # File Managers
            "files": "nautilus",
            "dolphin": "dolphin",
            "thunar": "thunar",
            "nemo": "nemo",
            
            # Editors
            "gedit": "gedit",
            "vscode": "code",
            "code": "code",
            "vim": "vim",
            "nvim": "nvim",
            "sublime": "subl",
            "atom": "atom",
            
            # Media
            "vlc": "vlc",
            "mpv": "mpv",
            "spotify": "spotify",
            
            # System
            "settings": "gnome-control-center",
            "system monitor": "gnome-system-monitor",
            "htop": "htop",
            "btop": "btop",
            
            # Communication
            "discord": "discord",
            "telegram": "telegram-desktop",
            "slack": "slack",
            
            # Development
            "docker": "docker",
            "git": "git",
            "postman": "postman",
        }
        
        # Desktop file locations
        self.desktop_dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
        ]
        
        self._build_desktop_cache()
        logger.info("ApplicationLauncher initialized")
    
    def _build_desktop_cache(self):
        """Build cache of available .desktop applications"""
        self.desktop_cache = {}
        
        for desktop_dir in self.desktop_dirs:
            if not os.path.exists(desktop_dir):
                continue
            
            try:
                for file in os.listdir(desktop_dir):
                    if file.endswith(".desktop"):
                        filepath = os.path.join(desktop_dir, file)
                        app_info = self._parse_desktop_file(filepath)
                        if app_info and app_info.get("exec"):
                            name = app_info.get("name", file.replace(".desktop", "")).lower()
                            self.desktop_cache[name] = app_info
            except Exception as e:
                logger.warning(f"Failed to scan {desktop_dir}: {e}")
        
        logger.debug(f"Cached {len(self.desktop_cache)} desktop applications")
    
    def _parse_desktop_file(self, filepath: str) -> Optional[Dict]:
        """Parse a .desktop file"""
        try:
            info = {}
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("Name="):
                        info["name"] = line[5:]
                    elif line.startswith("Exec="):
                        info["exec"] = line[5:].split("%")[0].strip()
                    elif line.startswith("Comment="):
                        info["comment"] = line[8:]
                    elif line.startswith("Categories="):
                        info["categories"] = line[11:]
                    elif line.startswith("Icon="):
                        info["icon"] = line[5:]
                    elif line.startswith("Terminal="):
                        info["terminal"] = line[9:].lower() == "true"
                    elif line.startswith("NoDisplay="):
                        info["nodisplay"] = line[10:].lower() == "true"
            
            if info.get("nodisplay"):
                return None
            return info
        except Exception as e:
            logger.debug(f"Failed to parse {filepath}: {e}")
            return None
    
    def open_browser(self, url: str = "") -> str:
        """Open web browser"""
        cmd = self.commands["browser"]
        if url:
            cmd = f"{cmd} {url}"
        return self._launch(cmd, "browser")
    
    def open_terminal(self, command: str = "", directory: str = "") -> str:
        """Open terminal"""
        cmd = self.commands["terminal"]
        
        # Handle different terminal emulators
        if "gnome-terminal" in cmd:
            if command:
                cmd += f" -- {command}"
            if directory:
                cmd += f" --working-directory={directory}"
        elif "konsole" in cmd:
            if command:
                cmd += f" -e {command}"
            if directory:
                cmd += f" --workdir {directory}"
        elif "alacritty" in cmd or "kitty" in cmd:
            if directory:
                cmd += f" --working-directory {directory}"
            if command:
                cmd += f" -e {command}"
        
        return self._launch(cmd, "terminal")
    
    def open_file_manager(self, path: str = "") -> str:
        """Open file manager"""
        cmd = self.commands["file_manager"]
        if path:
            cmd = f"{cmd} {path}"
        return self._launch(cmd, "file manager")
    
    def open_text_editor(self, file_path: str = "") -> str:
        """Open text editor"""
        cmd = self.commands["text_editor"]
        if file_path:
            cmd = f"{cmd} {file_path}"
        return self._launch(cmd, "text editor")
    
    def open_code_editor(self, path: str = "") -> str:
        """Open code editor (VS Code by default)"""
        cmd = self.commands["code_editor"]
        if path:
            cmd = f"{cmd} {path}"
        return self._launch(cmd, "code editor")
    
    def open_application(self, app_name: str, args: str = "") -> str:
        """Open application by name"""
        app_name_lower = app_name.lower().strip()
        
        # Check direct mapping
        if app_name_lower in self.app_map:
            cmd = self.app_map[app_name_lower]
            if args:
                cmd += f" {args}"
            return self._launch(cmd, app_name)
        
        # Check desktop cache
        if app_name_lower in self.desktop_cache:
            app_info = self.desktop_cache[app_name_lower]
            cmd = app_info["exec"]
            if args:
                cmd += f" {args}"
            return self._launch(cmd, app_name)
        
        # Try fuzzy matching
        matches = self._fuzzy_match(app_name_lower)
        if matches:
            best_match = matches[0]
            app_info = self.desktop_cache[best_match]
            cmd = app_info["exec"]
            if args:
                cmd += f" {args}"
            return self._launch(cmd, best_match)
        
        # Try as direct command
        if shutil.which(app_name_lower):
            cmd = app_name_lower
            if args:
                cmd += f" {args}"
            return self._launch(cmd, app_name)
        
        return f"Application not found: {app_name}. Available: {', '.join(list(self.app_map.keys())[:10])}..."
    
    def close_application(self, app_name: str) -> str:
        """Close application by name"""
        app_name_lower = app_name.lower()
        closed = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_name = proc.info['name'].lower() if proc.info['name'] else ""
                cmdline = " ".join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                
                if app_name_lower in proc_name or app_name_lower in cmdline:
                    proc.terminate()
                    closed.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed:
            return f"Closed: {', '.join(set(closed))}"
        return f"No running process found for: {app_name}"
    
    def list_running_applications(self) -> List[Dict]:
        """List currently running GUI applications"""
        apps = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['name'] and proc.info['cpu_percent'] > 0:
                    apps.append({
                        "name": proc.info['name'],
                        "pid": proc.info['pid'],
                        "cpu": proc.info['cpu_percent'],
                        "memory": proc.info['memory_percent'],
                        "cmdline": " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return sorted(apps, key=lambda x: x['cpu'], reverse=True)[:20]
    
    def search_applications(self, query: str) -> List[Dict]:
        """Search for applications"""
        query = query.lower()
        results = []
        
        # Search app map
        for name, cmd in self.app_map.items():
            if query in name:
                results.append({"name": name, "command": cmd, "source": "map"})
        
        # Search desktop cache
        for name, info in self.desktop_cache.items():
            if query in name or (info.get("comment") and query in info["comment"].lower()):
                results.append({
                    "name": info.get("name", name),
                    "command": info.get("exec", ""),
                    "comment": info.get("comment", ""),
                    "source": "desktop"
                })
        
        return results[:20]
    
    def _launch(self, command: str, name: str) -> str:
        """Launch a command in background"""
        try:
            # Use subprocess.Popen for background execution
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"Launched {name}: {command}")
            return f"Opening {name}..."
        except Exception as e:
            logger.error(f"Failed to launch {name}: {e}")
            return f"Failed to open {name}: {str(e)}"
    
    def _fuzzy_match(self, query: str) -> List[str]:
        """Simple fuzzy matching for app names"""
        matches = []
        for name in self.desktop_cache.keys():
            if query in name or name in query:
                matches.append(name)
            # Simple character overlap scoring
            elif len(set(query) & set(name)) > len(query) * 0.5:
                matches.append(name)
        return matches
    
    def set_default(self, app_type: str, command: str) -> str:
        """Set default application for a type"""
        if app_type in self.commands:
            old = self.commands[app_type]
            self.commands[app_type] = command
            # Update environment variable
            env_var = {
                "browser": "BROWSER_COMMAND",
                "terminal": "TERMINAL_COMMAND",
                "file_manager": "FILE_MANAGER_COMMAND",
                "text_editor": "TEXT_EDITOR_COMMAND",
                "code_editor": "CODE_EDITOR_COMMAND"
            }.get(app_type)
            if env_var:
                os.environ[env_var] = command
            return f"Default {app_type} changed from '{old}' to '{command}'"
        return f"Unknown app type: {app_type}"
    
    def get_defaults(self) -> Dict[str, str]:
        """Get current default applications"""
        return self.commands.copy()
    
    def test(self) -> bool:
        """Test application launcher"""
        try:
            # Check if common commands exist
            for name, cmd in self.commands.items():
                if shutil.which(cmd.split()[0]):
                    logger.debug(f"{name}: {cmd} - OK")
                else:
                    logger.warning(f"{name}: {cmd} - NOT FOUND")
            return True
        except Exception as e:
            logger.error(f"Application launcher test failed: {e}")
            return False


class ProcessManager:
    """Advanced process management"""
    
    def __init__(self):
        pass
    
    def kill_process(self, identifier: str, by_name: bool = True) -> str:
        """Kill process by name or PID"""
        killed = []
        
        try:
            if by_name:
                for proc in psutil.process_iter(['pid', 'name']):
                    if identifier.lower() in proc.info['name'].lower():
                        proc.kill()
                        killed.append(f"{proc.info['name']} (PID: {proc.info['pid']})")
            else:
                # By PID
                pid = int(identifier)
                proc = psutil.Process(pid)
                name = proc.name()
                proc.kill()
                killed.append(f"{name} (PID: {pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError) as e:
            return f"Failed to kill process: {e}"
        
        if killed:
            return f"Killed: {', '.join(killed)}"
        return f"No process found matching: {identifier}"
    
    def get_process_info(self, identifier: str) -> Dict:
        """Get detailed process information"""
        try:
            if identifier.isdigit():
                proc = psutil.Process(int(identifier))
            else:
                procs = [p for p in psutil.process_iter(['pid', 'name']) 
                        if identifier.lower() in p.info['name'].lower()]
                if not procs:
                    return {"error": "Process not found"}
                proc = procs[0]
            
            with proc.oneshot():
                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe(),
                    "cmdline": proc.cmdline(),
                    "status": proc.status(),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_percent": proc.memory_percent(),
                    "memory_info": dict(proc.memory_info()._asdict()),
                    "create_time": proc.create_time(),
                    "num_threads": proc.num_threads(),
                    "username": proc.username(),
                }
        except Exception as e:
            return {"error": str(e)}
    
    def set_priority(self, identifier: str, priority: str) -> str:
        """Set process priority (nice value)"""
        priority_map = {
            "low": 19,
            "below_normal": 10,
            "normal": 0,
            "above_normal": -5,
            "high": -10,
            "realtime": -20
        }
        
        nice_value = priority_map.get(priority.lower())
        if nice_value is None:
            return f"Invalid priority. Options: {list(priority_map.keys())}"
        
        try:
            if identifier.isdigit():
                proc = psutil.Process(int(identifier))
            else:
                procs = [p for p in psutil.process_iter(['pid', 'name']) 
                        if identifier.lower() in p.info['name'].lower()]
                if not procs:
                    return "Process not found"
                proc = procs[0]
            
            proc.nice(nice_value)
            return f"Set priority of {proc.name()} (PID: {proc.pid}) to {priority}"
        except Exception as e:
            return f"Failed to set priority: {e}"