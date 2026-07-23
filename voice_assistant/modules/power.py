"""
Power Management Module
Handles system power operations: shutdown, reboot, suspend, hibernate, lock, logout
"""

import os
import logging
import subprocess
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PowerManager:
    """Manages system power operations"""
    
    def __init__(self):
        self.shutdown_cmd = os.getenv("SHUTDOWN_COMMAND", "systemctl poweroff")
        self.reboot_cmd = os.getenv("REBOOT_COMMAND", "systemctl reboot")
        self.suspend_cmd = os.getenv("SUSPEND_COMMAND", "systemctl suspend")
        self.hibernate_cmd = os.getenv("HIBERNATE_COMMAND", "systemctl hibernate")
        self.lock_cmd = os.getenv("LOCK_COMMAND", "gnome-screensaver-command -l")
        self.logout_cmd = os.getenv("LOGOUT_COMMAND", "gnome-session-quit --no-prompt")
        
        # Try to detect desktop environment for better lock/logout commands
        self.desktop_env = self._detect_desktop_environment()
        self._adjust_commands_for_de()
        
        logger.info(f"PowerManager initialized for {self.desktop_env}")
    
    def _detect_desktop_environment(self) -> str:
        """Detect the current desktop environment"""
        de = os.getenv("XDG_CURRENT_DESKTOP", "").lower()
        if not de:
            de = os.getenv("DESKTOP_SESSION", "").lower()
        
        if "gnome" in de or "ubuntu" in de:
            return "gnome"
        elif "kde" in de or "plasma" in de:
            return "kde"
        elif "xfce" in de or "xubuntu" in de:
            return "xfce"
        elif "mate" in de:
            return "mate"
        elif "cinnamon" in de:
            return "cinnamon"
        elif "i3" in de or "sway" in de:
            return "i3"
        elif "hyprland" in de:
            return "hyprland"
        else:
            return "unknown"
    
    def _adjust_commands_for_de(self):
        """Adjust commands based on desktop environment"""
        de_commands = {
            "gnome": {
                "lock": "gnome-screensaver-command -l",
                "logout": "gnome-session-quit --no-prompt"
            },
            "kde": {
                "lock": "qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock",
                "logout": "qdbus org.kde.ksmserver /KSMServer logout 0 0 0"
            },
            "xfce": {
                "lock": "xflock4",
                "logout": "xfce4-session-logout --logout"
            },
            "mate": {
                "lock": "mate-screensaver-command -l",
                "logout": "mate-session-save --logout-dialog"
            },
            "cinnamon": {
                "lock": "cinnamon-screensaver-command -l",
                "logout": "cinnamon-session-quit --logout --no-prompt"
            },
            "i3": {
                "lock": "i3lock",
                "logout": "i3-msg exit"
            },
            "hyprland": {
                "lock": "hyprlock",
                "logout": "hyprctl dispatch exit"
            }
        }
        
        if self.desktop_env in de_commands:
            self.lock_cmd = de_commands[self.desktop_env]["lock"]
            self.logout_cmd = de_commands[self.desktop_env]["logout"]
    
    def _run_command(self, cmd: str, sudo: bool = False) -> Dict[str, Any]:
        """Run a system command and return result"""
        try:
            if sudo:
                cmd = f"sudo {cmd}"
            
            logger.info(f"Executing: {cmd}")
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {cmd}")
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            logger.error(f"Command error: {e}")
            return {"success": False, "error": str(e)}
    
    def shutdown(self, delay: int = 0, force: bool = False) -> str:
        """Shutdown the system"""
        if delay > 0:
            cmd = f"shutdown -h +{delay}"
            if force:
                cmd += " -f"
            result = self._run_command(cmd, sudo=True)
            if result["success"]:
                return f"System will shutdown in {delay} minute(s)."
            return f"Failed to schedule shutdown: {result.get('stderr', 'Unknown error')}"
        else:
            # Immediate shutdown
            cmd = self.shutdown_cmd
            if force:
                cmd = "systemctl poweroff -f"
            result = self._run_command(cmd, sudo=True)
            if result["success"]:
                return "Shutting down system..."
            return f"Shutdown failed: {result.get('stderr', 'Unknown error')}"
    
    def reboot(self, delay: int = 0, force: bool = False) -> str:
        """Reboot the system"""
        if delay > 0:
            cmd = f"shutdown -r +{delay}"
            if force:
                cmd += " -f"
            result = self._run_command(cmd, sudo=True)
            if result["success"]:
                return f"System will reboot in {delay} minute(s)."
            return f"Failed to schedule reboot: {result.get('stderr', 'Unknown error')}"
        else:
            cmd = self.reboot_cmd
            if force:
                cmd = "systemctl reboot -f"
            result = self._run_command(cmd, sudo=True)
            if result["success"]:
                return "Rebooting system..."
            return f"Reboot failed: {result.get('stderr', 'Unknown error')}"
    
    def suspend(self) -> str:
        """Suspend the system (sleep)"""
        result = self._run_command(self.suspend_cmd)
        if result["success"]:
            return "Suspending system..."
        return f"Suspend failed: {result.get('stderr', 'Unknown error')}"
    
    def hibernate(self) -> str:
        """Hibernate the system"""
        result = self._run_command(self.hibernate_cmd)
        if result["success"]:
            return "Hibernating system..."
        return f"Hibernate failed: {result.get('stderr', 'Unknown error')}"
    
    def lock(self) -> str:
        """Lock the screen"""
        result = self._run_command(self.lock_cmd)
        if result["success"]:
            return "Screen locked."
        return f"Lock failed: {result.get('stderr', 'Unknown error')}"
    
    def logout(self) -> str:
        """Logout current user"""
        result = self._run_command(self.logout_cmd)
        if result["success"]:
            return "Logging out..."
        return f"Logout failed: {result.get('stderr', 'Unknown error')}"
    
    def cancel_shutdown(self) -> str:
        """Cancel a scheduled shutdown/reboot"""
        result = self._run_command("shutdown -c", sudo=True)
        if result["success"]:
            return "Scheduled shutdown cancelled."
        return f"Cancel failed: {result.get('stderr', 'Unknown error')}"
    
    def get_power_status(self) -> Dict[str, Any]:
        """Get power/battery status"""
        import psutil
        
        battery = psutil.sensors_battery()
        status = {
            "battery_percent": battery.percent if battery else None,
            "battery_plugged": battery.power_plugged if battery else None,
            "battery_time_left": battery.secsleft if battery else None,
            "on_ac_power": battery.power_plugged if battery else None
        }
        
        # Format time left
        if status["battery_time_left"] and status["battery_time_left"] != psutil.POWER_TIME_UNLIMITED:
            hours = status["battery_time_left"] // 3600
            minutes = (status["battery_time_left"] % 3600) // 60
            status["battery_time_formatted"] = f"{hours}h {minutes}m"
        else:
            status["battery_time_formatted"] = "Unknown" if battery else "No battery"
        
        return status
    
    def test(self) -> bool:
        """Test power commands (dry run)"""
        try:
            # Test if commands exist
            commands_to_test = [
                ("systemctl", ["systemctl", "--version"]),
                ("shutdown", ["shutdown", "--version"]),
            ]
            
            for name, cmd in commands_to_test:
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    logger.warning(f"{name} command not available")
            
            logger.info("Power manager test completed")
            return True
        except Exception as e:
            logger.error(f"Power manager test failed: {e}")
            return False


class PowerProfileManager:
    """Manage power profiles (performance, balanced, power-saver)"""
    
    def __init__(self):
        self.profiles = {
            "performance": self._set_performance,
            "balanced": self._set_balanced,
            "powersave": self._set_powersave
        }
        self.current_profile = "balanced"
    
    def set_profile(self, profile: str) -> str:
        """Set power profile"""
        profile = profile.lower()
        if profile not in self.profiles:
            return f"Unknown profile: {profile}. Available: {list(self.profiles.keys())}"
        
        try:
            self.profiles[profile]()
            self.current_profile = profile
            return f"Power profile set to: {profile}"
        except Exception as e:
            logger.error(f"Failed to set power profile: {e}")
            return f"Failed to set profile: {e}"
    
    def get_profile(self) -> str:
        """Get current power profile"""
        return self.current_profile
    
    def _set_performance(self):
        """Set performance profile"""
        # CPU governor
        self._set_cpu_governor("performance")
        # GPU performance (if NVIDIA)
        self._set_nvidia_performance()
    
    def _set_balanced(self):
        """Set balanced profile"""
        self._set_cpu_governor("powersave")  # or ondemand
    
    def _set_powersave(self):
        """Set power saving profile"""
        self._set_cpu_governor("powersave")
        # Reduce screen brightness
        # Disable unnecessary services
    
    def _set_cpu_governor(self, governor: str):
        """Set CPU frequency governor"""
        try:
            import glob
            cpu_dirs = glob.glob("/sys/devices/system/cpu/cpu[0-9]*")
            for cpu_dir in cpu_dirs:
                gov_path = f"{cpu_dir}/cpufreq/scaling_governor"
                if os.path.exists(gov_path):
                    with open(gov_path, 'w') as f:
                        f.write(governor)
        except Exception as e:
            logger.warning(f"Could not set CPU governor: {e}")
    
    def _set_nvidia_performance(self):
        """Set NVIDIA GPU to performance mode"""
        try:
            subprocess.run(["nvidia-settings", "-a", "[gpu:0]/GPUPowerMizerMode=1"], 
                         capture_output=True)
        except:
            pass