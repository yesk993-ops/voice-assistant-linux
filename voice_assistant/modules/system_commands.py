"""
System Commands Module
Handles system-level commands: updates, shutdown timer, custom commands, uptime, users
"""

import os
import logging
import subprocess
import time
import shlex
from typing import Dict, List, Optional, Any
import psutil

logger = logging.getLogger(__name__)


class SystemCommandsManager:
    """Manages system commands and operations"""
    
    def __init__(self):
        self.update_command = os.getenv("UPDATE_COMMAND", "sudo apt update && sudo apt upgrade -y")
        self.pacman_update = os.getenv("PACMAN_UPDATE_COMMAND", "sudo pacman -Syu")
        self.dnf_update = os.getenv("DNF_UPDATE_COMMAND", "sudo dnf upgrade -y")
        self.shutdown_timer_pid = None
        logger.info("SystemCommandsManager initialized")
    
    def run_update(self, distro: str = "auto", dry_run: bool = False) -> str:
        """Run system update"""
        try:
            if distro == "auto":
                distro = self._detect_distro()
            
            commands = {
                "ubuntu": self.update_command,
                "debian": self.update_command,
                "mint": self.update_command,
                "pop": self.update_command,
                "arch": self.pacman_update,
                "manjaro": self.pacman_update,
                "endeavour": self.pacman_update,
                "fedora": self.dnf_update,
                "rhel": "sudo dnf upgrade -y",
                "centos": "sudo dnf upgrade -y",
                "opensuse": "sudo zypper refresh && sudo zypper update -y",
            }
            
            cmd = commands.get(distro.lower(), self.update_command)
            
            if dry_run:
                return f"Dry run - would execute: {cmd}"
            
            logger.info(f"Running system update for {distro}: {cmd}")
            
            # Run in background with output capture
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Wait for completion with timeout
            try:
                stdout, _ = process.communicate(timeout=300)  # 5 min timeout
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, _ = process.communicate()
                return f"Update timed out after 5 minutes. Partial output:\n{stdout[-2000:]}"
            
            if process.returncode == 0:
                return "System update completed successfully."
            else:
                return f"Update failed with code {process.returncode}:\n{stdout[-2000:]}"
        except Exception as e:
            logger.error(f"Update error: {e}")
            return f"Update failed: {str(e)}"
    
    def _detect_distro(self) -> str:
        """Detect Linux distribution"""
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
            
            if "ubuntu" in content or "mint" in content or "pop" in content:
                return "ubuntu"
            elif "debian" in content:
                return "debian"
            elif "arch" in content or "manjaro" in content or "endeavour" in content:
                return "arch"
            elif "fedora" in content:
                return "fedora"
            elif "rhel" in content or "red hat" in content:
                return "rhel"
            elif "centos" in content:
                return "centos"
            elif "opensuse" in content or "suse" in content:
                return "opensuse"
            else:
                return "ubuntu"  # Default
        except:
            return "ubuntu"
    
    def run_command(self, command: str, timeout: int = 30, 
                    capture_output: bool = True, shell: bool = True) -> Dict[str, Any]:
        """Run arbitrary shell command"""
        try:
            logger.info(f"Running command: {command}")
            
            if shell:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True
                )
            else:
                args = shlex.split(command)
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    text=True
                )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return {
                    "success": False,
                    "stdout": stdout or "",
                    "stderr": "Command timed out",
                    "returncode": -1
                }
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout or "",
                "stderr": stderr or "",
                "returncode": process.returncode
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def run_command_async(self, command: str) -> str:
        """Run command asynchronously (fire and forget)"""
        try:
            subprocess.Popen(command, shell=True, start_new_session=True)
            return f"Command started in background: {command}"
        except Exception as e:
            return f"Failed to start command: {str(e)}"
    
    def shutdown_timer(self, minutes: int) -> str:
        """Schedule shutdown in specified minutes"""
        try:
            if minutes <= 0:
                return "Invalid time. Must be positive minutes."
            
            # Cancel any existing shutdown
            self.cancel_shutdown()
            
            # Schedule new shutdown
            result = subprocess.run(
                ["shutdown", "-h", f"+{minutes}"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                self.shutdown_timer_pid = None  # shutdown command doesn't give PID easily
                return f"System will shutdown in {minutes} minute(s). Use 'cancel shutdown' to abort."
            return f"Failed to schedule shutdown: {result.stderr}"
        except Exception as e:
            logger.error(f"Shutdown timer error: {e}")
            return f"Failed to schedule shutdown: {str(e)}"
    
    def cancel_shutdown(self) -> str:
        """Cancel scheduled shutdown"""
        try:
            result = subprocess.run(
                ["shutdown", "-c"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return "Scheduled shutdown cancelled."
            return f"Failed to cancel shutdown: {result.stderr}"
        except Exception as e:
            logger.error(f"Cancel shutdown error: {e}")
            return f"Failed to cancel shutdown: {str(e)}"
    
    def get_shutdown_status(self) -> str:
        """Check if shutdown is scheduled"""
        try:
            # Check /run/systemd/shutdown/scheduled
            shutdown_file = Path("/run/systemd/shutdown/scheduled")
            if shutdown_file.exists():
                content = shutdown_file.read_text().strip()
                return f"Shutdown scheduled: {content}"
            
            # Alternative: check shutdown_file = Path("/run/nologin")
            if _file.exists():
                return "Shutdown scheduled (nologin file exists)"
            
            return "No shutdown scheduled"
        except Exception as e:
            return f"Could not check shutdown status: {str(e)}"
    
    def show_uptime(self) -> str:
        """Show system uptime"""
        try:
            # Use psutil
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime_seconds = current_time - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours > 0:
                parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            
            uptime_str = ", ".join(parts) if parts else "less than a minute"
            
            # Also get load average
            load1, load5, load15 = os.getloadavg()
            
            return (
                f"System uptime: {uptime_str}\n"
                f"Load average: {load1:.2f}, {load5:.2f}, {load15:.2f}"
            )
        except Exception as e:
            logger.error(f"Uptime error: {e}")
            return f"Failed to get uptime: {str(e)}"
    
    def show_users(self) -> str:
        """Show logged in users"""
        try:
            users = psutil.users()
            
            if not users:
                return "No users currently logged in"
            
            lines = ["Logged in users:"]
            for user in users:
                login_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(user.started))
                lines.append(
                    f"  {user.name} on {user.terminal or '?'} "
                    f"from {user.host or 'local'} since {login_time}"
                )
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Show users error: {e}")
            return f"Failed to get users: {str(e)}"
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            info = {
                "hostname": os.uname().nodename,
                "kernel": os.uname().release,
                "architecture": os.uname().machine,
                "os": self._get_os_info(),
                "uptime": self.show_uptime(),
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "memory_total": psutil.virtual_memory().total,
                "disk_partitions": len(psutil.disk_partitions()),
            }
            return info
        except Exception as e:
            logger.error(f"System info error: {e}")
            return {"error": str(e)}
    
    def _get_os_info(self) -> str:
        """Get OS information"""
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except:
            pass
        return "Unknown"
    
    def install_package(self, package: str, manager: str = "auto") -> str:
        """Install package using system package manager"""
        try:
            if manager == "auto":
                manager = self._detect_package_manager()
            
            commands = {
                "apt": f"sudo apt install -y {package}",
                "pacman": f"sudo pacman -S --noconfirm {package}",
                "dnf": f"sudo dnf install -y {package}",
                "zypper": f"sudo zypper install -y {package}",
                "flatpak": f"flatpak install -y {package}",
                "snap": f"sudo snap install {package}",
            }
            
            cmd = commands.get(manager, commands["apt"])
            return self.run_command(cmd, timeout=120)["stdout"]
        except Exception as e:
            return f"Install failed: {str(e)}"
    
    def remove_package(self, package: str, manager: str = "auto") -> str:
        """Remove package"""
        try:
            if manager == "auto":
                manager = self._detect_package_manager()
            
            commands = {
                "apt": f"sudo apt remove -y {package}",
                "pacman": f"sudo pacman -R --noconfirm {package}",
                "dnf": f"sudo dnf remove -y {package}",
                "zypper": f"sudo zypper remove -y {package}",
                "flatpak": f"flatpak uninstall -y {package}",
                "snap": f"sudo snap remove {package}",
            }
            
            cmd = commands.get(manager, commands["apt"])
            return self.run_command(cmd, timeout=60)["stdout"]
        except Exception as e:
            return f"Remove failed: {str(e)}"
    
    def _detect_package_manager(self) -> str:
        """Detect package manager"""
        managers = ["apt", "pacman", "dnf", "zypper"]
        for m in managers:
            if shutil.which(m):
                return m
        return "apt"
    
    def search_package(self, query: str, manager: str = "auto") -> str:
        """Search for package"""
        try:
            if manager == "auto":
                manager = self._detect_package_manager()
            
            commands = {
                "apt": f"apt search {query}",
                "pacman": f"pacman -Ss {query}",
                "dnf": f"dnf search {query}",
                "zypper": f"zypper search {query}",
            }
            
            cmd = commands.get(manager, commands["apt"])
            result = self.run_command(cmd, timeout=30)
            return result["stdout"] if result["success"] else result["stderr"]
        except Exception as e:
            return f"Search failed: {str(e)}"
    
    def list_installed_packages(self, manager: str = "auto", limit: int = 50) -> str:
        """List installed packages"""
        try:
            if manager == "auto":
                manager = self._detect_package_manager()
            
            commands = {
                "apt": "apt list --installed",
                "pacman": "pacman -Q",
                "dnf": "dnf list installed",
                "zypper": "zypper se --installed-only",
            }
            
            cmd = commands.get(manager, commands["apt"])
            result = self.run_command(cmd, timeout=30)
            
            if result["success"]:
                lines = result["stdout"].strip().split('\n')
                if len(lines) > limit:
                    lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
                return "\n".join(lines)
            return result["stderr"]
        except Exception as e:
            return f"List packages failed: {str(e)}"
    
    def run_systemd_command(self, action: str, service: str) -> str:
        """Control systemd services"""
        valid_actions = ["start", "stop", "restart", "enable", "disable", "status"]
        
        if action not in valid_actions:
            return f"Invalid action: {action}. Valid: {', '.join(valid_actions)}"
        
        try:
            cmd = f"sudo systemctl {action} {service}"
            result = self.run_command(cmd, timeout=30)
            
            if result["success"]:
                return f"Service {service} {action}ed successfully"
            return f"Failed: {result['stderr']}"
        except Exception as e:
            return f"Systemd command failed: {str(e)}"
    
    def list_systemd_services(self, state: str = "running") -> str:
        """List systemd services"""
        try:
            cmd = f"systemctl list-units --type=service --state={state} --no-legend"
            result = self.run_command(cmd, timeout=30)
            
            if result["success"]:
                lines = result["stdout"].strip().split('\n')
                if len(lines) > 30:
                    lines = lines[:30] + [f"... ({len(lines) - 30} more)"]
                return "\n".join(lines)
            return result["stderr"]
        except Exception as e:
            return f"List services failed: {str(e)}"
    
    def get_failed_services(self) -> str:
        """Get failed systemd services"""
        return self.list_systemd_services("failed")
    
    def test(self) -> bool:
        """Test system commands"""
        try:
            self.show_uptime()
            self.show_users()
            self.run_command("echo test", timeout=5)
            logger.info("System commands test passed")
            return True
        except Exception as e:
            logger.error(f"System commands test failed: {e}")
            return False