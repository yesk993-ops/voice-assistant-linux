"""
System Monitor Module
Monitors CPU, memory, disk, network, temperature, battery, processes
"""

import os
import logging
import psutil
import platform
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system resources and health"""
    
    def __init__(self):
        self.network_interface = os.getenv("NETWORK_INTERFACE", "auto")
        self._last_net_io = None
        self._last_net_time = None
        logger.info("SystemMonitor initialized")
    
    def get_cpu_usage(self, interval: float = 1.0, per_cpu: bool = False) -> str:
        """Get CPU usage"""
        try:
            if per_cpu:
                usage = psutil.cpu_percent(interval=interval, percpu=True)
                lines = ["CPU Usage (per core):"]
                for i, u in enumerate(usage):
                    bar = self._make_bar(u)
                    lines.append(f"  CPU {i}: {u:5.1f}% {bar}")
                return "\n".join(lines)
            else:
                usage = psutil.cpu_percent(interval=interval)
                bar = self._make_bar(usage)
                
                # Get frequency info
                freq = psutil.cpu_freq()
                freq_str = ""
                if freq:
                    freq_str = f" @ {freq.current:.0f}MHz"
                
                # Get load average
                load1, load5, load15 = os.getloadavg()
                
                return (
                    f"CPU Usage: {usage:.1f}%{freq_str} {bar}\n"
                    f"Load Average: {load1:.2f}, {load5:.2f}, {load15:.2f}\n"
                    f"Cores: {psutil.cpu_count(logical=True)} logical, {psutil.cpu_count(logical=False)} physical"
                )
        except Exception as e:
            logger.error(f"CPU usage error: {e}")
            return f"Failed to get CPU usage: {str(e)}"
    
    def get_memory_usage(self) -> str:
        """Get memory usage"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            mem_bar = self._make_bar(mem.percent)
            swap_bar = self._make_bar(swap.percent)
            
            lines = [
                f"Memory Usage: {mem.percent:.1f}% {mem_bar}",
                f"  Total: {self._format_bytes(mem.total)}",
                f"  Used:  {self._format_bytes(mem.used)}",
                f"  Free:  {self._format_bytes(mem.available)}",
                f"  Buffers/Cache: {self._format_bytes(mem.buffers + mem.cached) if hasattr(mem, 'buffers') else 'N/A'}",
                "",
                f"Swap Usage: {swap.percent:.1f}% {swap_bar}",
                f"  Total: {self._format_bytes(swap.total)}",
                f"  Used:  {self._format_bytes(swap.used)}",
                f"  Free:  {self._format_bytes(swap.free)}",
            ]
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Memory usage error: {e}")
            return f"Failed to get memory usage: {str(e)}"
    
    def get_disk_usage(self, path: str = "/") -> str:
        """Get disk usage for all mounts or specific path"""
        try:
            if path == "all" or path == "":
                partitions = psutil.disk_partitions()
                lines = ["Disk Usage:"]
                
                for part in partitions:
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        percent = (usage.used / usage.total) * 100
                        bar = self._make_bar(percent)
                        
                        lines.append(
                            f"  {part.device} ({part.mountpoint}) [{part.fstype}]\n"
                            f"    {percent:.1f}% {bar} "
                            f"{self._format_bytes(usage.used)}/{self._format_bytes(usage.total)}"
                        )
                    except PermissionError:
                        lines.append(f"  {part.device} ({part.mountpoint}) - Permission denied")
                    except Exception:
                        lines.append(f"  {part.device} ({part.mountpoint}) - Error reading")
                
                return "\n".join(lines)
            else:
                usage = psutil.disk_usage(path)
                percent = (usage.used / usage.total) * 100
                bar = self._make_bar(percent)
                
                return (
                    f"Disk Usage for {path}:\n"
                    f"  {percent:.1f}% {bar}\n"
                    f"  Used: {self._format_bytes(usage.used)}\n"
                    f"  Free: {self._format_bytes(usage.free)}\n"
                    f"  Total: {self._format_bytes(usage.total)}"
                )
        except Exception as e:
            logger.error(f"Disk usage error: {e}")
            return f"Failed to get disk usage: {str(e)}"
    
    def get_disk_io(self) -> str:
        """Get disk I/O statistics"""
        try:
            io = psutil.disk_io_counters()
            if not io:
                return "Disk I/O stats not available"
            
            return (
                f"Disk I/O:\n"
                f"  Read:  {self._format_bytes(io.read_bytes)} ({io.read_count} ops)\n"
                f"  Write: {self._format_bytes(io.write_bytes)} ({io.write_count} ops)\n"
                f"  Read time:  {io.read_time}ms\n"
                f"  Write time: {io.write_time}ms"
            )
        except Exception as e:
            return f"Failed to get disk I/O: {str(e)}"
    
    def get_temperature(self) -> str:
        """Get system temperatures"""
        try:
            temps = psutil.sensors_temperatures()
            
            if not temps:
                return "Temperature sensors not available"
            
            lines = ["System Temperatures:"]
            
            for name, entries in temps.items():
                lines.append(f"  {name}:")
                for entry in entries:
                    label = entry.label or "Core"
                    current = entry.current
                    high = entry.high
                    critical = entry.critical
                    
                    status = ""
                    if critical and current >= critical:
                        status = " 🔴 CRITICAL"
                    elif high and current >= high:
                        status = " 🟡 HIGH"
                    
                    lines.append(f"    {label}: {current:.1f}°C{status}")
                    if high:
                        lines[-1] += f" (high: {high:.1f}°C)"
                    if critical:
                        lines[-1] += f" (crit: {critical:.1f}°C)"
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Temperature error: {e}")
            return f"Failed to get temperatures: {str(e)}"
    
    def get_fan_speeds(self) -> str:
        """Get fan speeds"""
        try:
            fans = psutil.sensors_fans()
            
            if not fans:
                return "Fan sensors not available"
            
            lines = ["Fan Speeds:"]
            
            for name, entries in fans.items():
                lines.append(f"  {name}:")
                for entry in entries:
                    label = entry.label or "Fan"
                    speed = entry.current
                    lines.append(f"    {label}: {speed} RPM")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to get fan speeds: {str(e)}"
    
    def get_battery(self) -> str:
        """Get battery status"""
        try:
            battery = psutil.sensors_battery()
            
            if not battery:
                return "No battery detected"
            
            percent = battery.percent
            plugged = battery.power_plugged
            secs_left = battery.secsleft
            
            bar = self._make_bar(percent)
            status = "Charging" if plugged else "Discharging"
            
            time_str = ""
            if secs_left != psutil.POWER_TIME_UNLIMITED and secs_left != psutil.POWER_TIME_UNKNOWN:
                hours = secs_left // 3600
                minutes = (secs_left % 3600) // 60
                time_str = f"\n  Time remaining: {hours}h {minutes}m"
            elif plugged:
                time_str = "\n  Time remaining: Charging..."
            
            return (
                f"Battery: {percent:.1f}% {bar} ({status}){time_str}\n"
                f"  Power plugged: {'Yes' if plugged else 'No'}"
            )
        except Exception as e:
            logger.error(f"Battery error: {e}")
            return f"Failed to get battery: {str(e)}"
    
    def get_network_info(self, interface: str = "") -> str:
        """Get network interface information"""
        try:
            if interface == "auto" or not interface:
                # Get default interface
                addrs = psutil.net_if_addrs()
                stats = psutil.net_if_stats()
                
                # Find first UP interface with IPv4
                for iface, addr_list in addrs.items():
                    if stats.get(iface) and stats[iface].isup:
                        for addr in addr_list:
                            if addr.family == 2:  # AF_INET
                                interface = iface
                                break
                    if interface:
                        break
            
            if not interface:
                return "No active network interface found"
            
            # Get addresses
            addrs = psutil.net_if_addrs().get(interface, [])
            stats = psutil.net_if_stats().get(interface)
            io = psutil.net_io_counters(pernic=True).get(interface)
            
            lines = [f"Network Interface: {interface}"]
            
            if stats:
                lines.append(f"  Status: {'Up' if stats.isup else 'Down'}")
                lines.append(f"  Speed: {stats.speed} Mbps")
                lines.append(f"  MTU: {stats.mtu}")
            
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    lines.append(f"  IPv4: {addr.address}/{addr.netmask}")
                elif addr.family == 10:  # IPv6
                    lines.append(f"  IPv6: {addr.address}")
                elif addr.family == 17:  # MAC
                    lines.append(f"  MAC: {addr.address}")
            
            if io:
                lines.append(f"  RX: {self._format_bytes(io.bytes_recv)} ({io.packets_recv} packets)")
                lines.append(f"  TX: {self._format_bytes(io.bytes_sent)} ({io.packets_sent} packets)")
                lines.append(f"  Errors: RX={io.errin} TX={io.errout}")
                lines.append(f"  Drops: RX={io.dropin} TX={io.dropout}")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Network info error: {e}")
            return f"Failed to get network info: {str(e)}"
    
    def get_network_speed(self, interval: float = 1.0) -> str:
        """Get current network speed"""
        try:
            # Get initial counters
            io1 = psutil.net_io_counters()
            time.sleep(interval)
            io2 = psutil.net_io_counters()
            
            rx_speed = (io2.bytes_recv - io1.bytes_recv) / interval
            tx_speed = (io2.bytes_sent - io1.bytes_sent) / interval
            
            return (
                f"Network Speed:\n"
                f"  Download: {self._format_bytes(rx_speed)}/s\n"
                f"  Upload:   {self._format_bytes(tx_speed)}/s"
            )
        except Exception as e:
            return f"Failed to get network speed: {str(e)}"
    
    def get_top_processes(self, count: int = 10, sort_by: str = "cpu") -> str:
        """Get top processes by CPU or memory"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    proc.info['cpu_percent'] = proc.cpu_percent()
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            
            lines = [f"Top {count} processes by {sort_by.upper()}:"]
            lines.append(f"{'PID':>8} {'USER':<12} {'CPU%':>6} {'MEM%':>6} {'NAME'}")
            lines.append("-" * 60)
            
            for proc in processes[:count]:
                lines.append(
                    f"{proc['pid']:>8} {proc['username'][:12]:<12} "
                    f"{proc['cpu_percent']:>6.1f} {proc['memory_percent']:>6.1f} {proc['name']}"
                )
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Top processes error: {e}")
            return f"Failed to get processes: {str(e)}"
    
    def get_process_tree(self, pid: int = None) -> str:
        """Get process tree"""
        try:
            if pid is None:
                # Show init process tree
                pid = 1
            
            proc = psutil.Process(pid)
            lines = [f"Process tree for PID {pid} ({proc.name()}):"]
            self._build_process_tree(proc, lines, "")
            
            return "\n".join(lines[:50])  # Limit output
        except Exception as e:
            return f"Failed to get process tree: {str(e)}"
    
    def _build_process_tree(self, proc: psutil.Process, lines: List[str], prefix: str):
        """Recursively build process tree"""
        try:
            children = proc.children()
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{child.pid} {child.name()}")
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._build_process_tree(child, lines, new_prefix)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def get_system_summary(self) -> str:
        """Get comprehensive system summary"""
        try:
            lines = [
                "=" * 50,
                "SYSTEM SUMMARY",
                "=" * 50,
                ""
            ]
            
            # Basic info
            uname = platform.uname()
            lines.append(f"Hostname: {uname.node}")
            lines.append(f"OS: {uname.system} {uname.release}")
            lines.append(f"Architecture: {uname.machine}")
            lines.append(f"Python: {platform.python_version()}")
            lines.append("")
            
            # CPU
            lines.append(self.get_cpu_usage(interval=0.5))
            lines.append("")
            
            # Memory
            lines.append(self.get_memory_usage())
            lines.append("")
            
            # Disk
            lines.append(self.get_disk_usage(""))
            lines.append("")
            
            # Temperature
            lines.append(self.get_temperature())
            lines.append("")
            
            # Battery
            lines.append(self.get_battery())
            lines.append("")
            
            # Network
            lines.append(self.get_network_info())
            lines.append("")
            
            # Top processes
            lines.append(self.get_top_processes(5, "cpu"))
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"System summary error: {e}")
            return f"Failed to get system summary: {str(e)}"
    
    def get_io_stats(self) -> str:
        """Get I/O statistics"""
        try:
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            lines = ["I/O Statistics:"]
            
            if disk_io:
                lines.append("  Disk:")
                lines.append(f"    Read:  {self._format_bytes(disk_io.read_bytes)} ({disk_io.read_count} ops)")
                lines.append(f"    Write: {self._format_bytes(disk_io.write_bytes)} ({disk_io.write_count} ops)")
            
            if net_io:
                lines.append("  Network:")
                lines.append(f"    RX: {self._format_bytes(net_io.bytes_recv)} ({net_io.packets_recv} packets)")
                lines.append(f"    TX: {self._format_bytes(net_io.bytes_sent)} ({net_io.packets_sent} packets)")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to get I/O stats: {str(e)}"
    
    def get_sensors(self) -> str:
        """Get all sensor readings"""
        try:
            lines = ["Hardware Sensors:"]
            
            # Temperatures
            temps = psutil.sensors_temperatures()
            if temps:
                lines.append("\n  Temperatures:")
                for name, entries in temps.items():
                    for entry in entries:
                        label = entry.label or name
                        lines.append(f"    {label}: {entry.current:.1f}°C")
            
            # Fans
            fans = psutil.sensors_fans()
            if fans:
                lines.append("\n  Fans:")
                for name, entries in fans.items():
                    for entry in entries:
                        label = entry.label or name
                        lines.append(f"    {label}: {entry.current} RPM")
            
            # Battery
            battery = psutil.sensors_battery()
            if battery:
                lines.append(f"\n  Battery: {battery.percent:.1f}% ({'Charging' if battery.power_plugged else 'Discharging'})")
            
            if len(lines) == 1:
                return "No hardware sensors detected"
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to get sensors: {str(e)}"
    
    def watch_resources(self, duration: int = 10, interval: float = 1.0) -> str:
        """Watch resources for specified duration"""
        try:
            lines = [f"Watching resources for {duration}s (interval: {interval}s)..."]
            
            for i in range(int(duration / interval)):
                cpu = psutil.cpu_percent(interval=interval)
                mem = psutil.virtual_memory().percent
                lines.append(f"  [{i+1}] CPU: {cpu:5.1f}%  MEM: {mem:5.1f}%")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Watch failed: {str(e)}"
    
    def _make_bar(self, percent: float, width: int = 20) -> str:
        """Create a visual bar"""
        filled = int(percent / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}PB"
    
    def test(self) -> bool:
        """Test system monitor"""
        try:
            self.get_cpu_usage(interval=0.1)
            self.get_memory_usage()
            self.get_disk_usage()
            self.get_temperature()
            self.get_battery()
            self.get_network_info()
            self.get_top_processes(5)
            logger.info("System monitor test passed")
            return True
        except Exception as e:
            logger.error(f"System monitor test failed: {e}")
            return False