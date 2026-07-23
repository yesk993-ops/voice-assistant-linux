"""
System Settings Manager Module
Controls brightness, volume, screen resolution, and other system settings
"""

import os
import logging
import subprocess
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import screen_brightness_control as sbc

logger = logging.getLogger(__name__)


class SystemSettingsManager:
    """Manages system settings: brightness, volume, resolution"""
    
    def __init__(self):
        self.brightness_device = os.getenv("BRIGHTNESS_DEVICE", "intel_backlight")
        self.alsa_card = os.getenv("ALSA_CARD", "default")
        self.alsa_control = os.getenv("ALSA_CONTROL", "Master")
        logger.info("SystemSettingsManager initialized")
    
    # ==================== Brightness Control ====================
    
    def set_brightness(self, value: int, display: int = 0) -> str:
        """Set screen brightness (0-100)"""
        try:
            value = max(0, min(100, value))
            
            # Try screen-brightness-control first
            try:
                sbc.set_brightness(value, display=display)
                return f"Brightness set to {value}%"
            except:
                pass
            
            # Fallback to sysfs
            return self._set_brightness_sysfs(value)
        except Exception as e:
            logger.error(f"Set brightness error: {e}")
            return f"Failed to set brightness: {str(e)}"
    
    def _set_brightness_sysfs(self, value: int) -> str:
        """Set brightness via sysfs"""
        try:
            # Find backlight device
            backlight_path = Path("/sys/class/backlight")
            devices = list(backlight_path.iterdir())
            
            if not devices:
                return "No backlight device found"
            
            # Prefer the configured device
            device = None
            for d in devices:
                if self.brightness_device in d.name:
                    device = d
                    break
            
            if not device:
                device = devices[0]
            
            max_brightness_file = device / "max_brightness"
            brightness_file = device / "brightness"
            
            if not max_brightness_file.exists():
                return "Cannot read max brightness"
            
            max_brightness = int(max_brightness_file.read_text().strip())
            brightness = int((value / 100) * max_brightness)
            
            # Write brightness (may need sudo)
            try:
                brightness_file.write_text(str(brightness))
            except PermissionError:
                # Try with pkexec
                subprocess.run(
                    ["pkexec", "tee", str(brightness_file)],
                    input=str(brightness).encode(),
                    check=True
                )
            
            return f"Brightness set to {value}%"
        except Exception as e:
            logger.error(f"Sysfs brightness error: {e}")
            return f"Failed to set brightness via sysfs: {str(e)}"
    
    def get_brightness(self, display: int = 0) -> str:
        """Get current brightness"""
        try:
            brightness = sbc.get_brightness(display=display)
            if isinstance(brightness, list):
                brightness = brightness[0]
            return f"Current brightness: {brightness}%"
        except:
            # Fallback to sysfs
            return self._get_brightness_sysfs()
    
    def _get_brightness_sysfs(self) -> str:
        """Get brightness via sysfs"""
        try:
            backlight_path = Path("/sys/class/backlight")
            devices = list(backlight_path.iterdir())
            
            if not devices:
                return "No backlight device found"
            
            device = devices[0]
            max_brightness = int((device / "max_brightness").read_text().strip())
            current = int((device / "brightness").read_text().strip())
            percent = int((current / max_brightness) * 100)
            
            return f"Current brightness: {percent}%"
        except Exception as e:
            return f"Failed to get brightness: {str(e)}"
    
    def increase_brightness(self, step: int = 10, display: int = 0) -> str:
        """Increase brightness by step"""
        try:
            current = sbc.get_brightness(display=display)
            if isinstance(current, list):
                current = current[0]
            new_value = min(100, current + step)
            return self.set_brightness(new_value, display)
        except:
            return self.set_brightness(100, display)  # Fallback
    
    def decrease_brightness(self, step: int = 10, display: int = 0) -> str:
        """Decrease brightness by step"""
        try:
            current = sbc.get_brightness(display=display)
            if isinstance(current, list):
                current = current[0]
            new_value = max(0, current - step)
            return self.set_brightness(new_value, display)
        except:
            return self.set_brightness(0, display)  # Fallback
    
    def list_displays(self) -> str:
        """List available displays for brightness control"""
        try:
            displays = sbc.list_monitors()
            if not displays:
                return "No displays found for brightness control"
            return f"Available displays: {', '.join(displays)}"
        except:
            return "Could not list displays"
    
    # ==================== Volume Control ====================
    
    def set_volume(self, value: int) -> str:
        """Set system volume (0-100)"""
        try:
            value = max(0, min(100, value))
            
            # Try PulseAudio/PipeWire first (pactl)
            result = subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return f"Volume set to {value}%"
            
            # Fallback to ALSA (amixer)
            result = subprocess.run(
                ["amixer", "-c", self.alsa_card, "sset", self.alsa_control, f"{value}%"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return f"Volume set to {value}% (via ALSA)"
            
            return f"Failed to set volume: {result.stderr}"
        except Exception as e:
            logger.error(f"Set volume error: {e}")
            return f"Failed to set volume: {str(e)}"
    
    def get_volume(self) -> str:
        """Get current volume"""
        try:
            # Try PulseAudio/PipeWire
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Parse output: "Volume: front-left: 65536 / 100% / 0.00 dB, front-right: 65536 / 100% / 0.00 dB"
                import re
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    return f"Current volume: {match.group(1)}%"
            
            # Fallback to ALSA
            result = subprocess.run(
                ["amixer", "-c", self.alsa_card, "get", self.alsa_control],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                import re
                match = re.search(r'\[(\d+)%\]', result.stdout)
                if match:
                    return f"Current volume: {match.group(1)}% (via ALSA)"
            
            return "Could not determine volume"
        except Exception as e:
            logger.error(f"Get volume error: {e}")
            return f"Failed to get volume: {str(e)}"
    
    def increase_volume(self, step: int = 10) -> str:
        """Increase volume by step"""
        try:
            # Get current volume
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                import re
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    current = int(match.group(1))
                    new_value = min(100, current + step)
                    return self.set_volume(new_value)
            
            # Fallback
            return self.set_volume(100)
        except:
            return self.set_volume(100)
    
    def decrease_volume(self, step: int = 10) -> str:
        """Decrease volume by step"""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                import re
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    current = int(match.group(1))
                    new_value = max(0, current - step)
                    return self.set_volume(new_value)
            
            return self.set_volume(0)
        except:
            return self.set_volume(0)
    
    def mute_volume(self) -> str:
        """Mute system volume"""
        try:
            result = subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return "Volume muted"
            
            # ALSA fallback
            subprocess.run(
                ["amixer", "-c", self.alsa_card, "sset", self.alsa_control, "mute"],
                capture_output=True
            )
            return "Volume muted (via ALSA)"
        except Exception as e:
            return f"Failed to mute: {str(e)}"
    
    def unmute_volume(self) -> str:
        """Unmute system volume"""
        try:
            result = subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return "Volume unmuted"
            
            # ALSA fallback
            subprocess.run(
                ["amixer", "-c", self.alsa_card, "sset", self.alsa_control, "unmute"],
                capture_output=True
            )
            return "Volume unmuted (via ALSA)"
        except Exception as e:
            return f"Failed to unmute: {str(e)}"
    
    def toggle_mute(self) -> str:
        """Toggle mute state"""
        try:
            result = subprocess.run(
                ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Check current state
                state_result = subprocess.run(
                    ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                    capture_output=True, text=True
                )
                if "yes" in state_result.stdout.lower():
                    return "Volume muted"
                else:
                    return "Volume unmuted"
            
            return "Failed to toggle mute"
        except Exception as e:
            return f"Failed to toggle mute: {str(e)}"
    
    def get_mute_status(self) -> str:
        """Get mute status"""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                capture_output=True, text=True
            )
            
            if "yes" in result.stdout.lower():
                return "Volume is muted"
            else:
                return "Volume is not muted"
        except:
            return "Could not determine mute status"
    
    def list_audio_devices(self) -> str:
        """List available audio sinks/sources"""
        try:
            # List sinks (outputs)
            result = subprocess.run(
                ["pactl", "list", "short", "sinks"],
                capture_output=True, text=True
            )
            
            sinks = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # List sources (inputs)
            result = subprocess.run(
                ["pactl", "list", "short", "sources"],
                capture_output=True, text=True
            )
            
            sources = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            lines = ["Audio Output Devices (Sinks):"]
            for sink in sinks:
                lines.append(f"  {sink}")
            
            lines.append("\nAudio Input Devices (Sources):")
            for source in sources:
                lines.append(f"  {source}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Failed to list audio devices: {str(e)}"
    
    def set_default_sink(self, sink_name: str) -> str:
        """Set default audio output device"""
        try:
            result = subprocess.run(
                ["pactl", "set-default-sink", sink_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                return f"Default audio output set to: {sink_name}"
            return f"Failed to set default sink: {result.stderr}"
        except Exception as e:
            return f"Failed to set default sink: {str(e)}"
    
    # ==================== Screen Resolution ====================
    
    def set_resolution(self, width: int, height: int, rate: int = 60, 
                       display: str = "") -> str:
        """Set screen resolution"""
        try:
            # Use xrandr
            cmd = ["xrandr"]
            
            if display:
                cmd.extend(["--output", display])
            
            # Try to find matching mode
            mode = f"{width}x{height}"
            if rate:
                mode += f"@{rate}"
            
            cmd.extend(["--mode", mode])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Resolution set to {width}x{height}@{rate}Hz"
            return f"Failed to set resolution: {result.stderr}"
        except Exception as e:
            logger.error(f"Set resolution error: {e}")
            return f"Failed to set resolution: {str(e)}"
    
    def get_resolution(self) -> str:
        """Get current screen resolution"""
        try:
            result = subprocess.run(
                ["xrandr", "--current"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '*' in line and '+' in line:
                        # Current mode line
                        parts = line.strip().split()
                        if parts:
                            return f"Current resolution: {parts[0]}"
            
            return "Could not determine resolution"
        except Exception as e:
            return f"Failed to get resolution: {str(e)}"
    
    def list_resolutions(self, display: str = "") -> str:
        """List available resolutions"""
        try:
            cmd = ["xrandr"]
            if display:
                cmd.extend(["--output", display])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                resolutions = []
                current_display = ""
                
                for line in lines:
                    line = line.strip()
                    if ' connected' in line:
                        current_display = line.split()[0]
                    elif current_display and 'x' in line and not line.startswith(' '):
                        # This is a mode line
                        parts = line.split()
                        if parts:
                            resolutions.append(f"  {current_display}: {parts[0]}")
                
                if resolutions:
                    return "Available resolutions:\n" + "\n".join(resolutions)
            
            return "Could not list resolutions"
        except Exception as e:
            return f"Failed to list resolutions: {str(e)}"
    
    def set_display_mode(self, display: str, mode: str) -> str:
        """Set display mode (on, off, auto, left-of, right-of, above, below)"""
        try:
            cmd = ["xrandr", "--output", display]
            
            if mode == "off":
                cmd.append("--off")
            elif mode == "auto":
                cmd.append("--auto")
            elif mode in ["left-of", "right-of", "above", "below"]:
                # Need another display
                return "Relative positioning requires a second display parameter"
            else:
                return f"Unknown mode: {mode}"
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Display {display} set to {mode}"
            return f"Failed: {result.stderr}"
        except Exception as e:
            return f"Failed to set display mode: {str(e)}"
    
    def set_multiple_displays(self, config: Dict[str, Dict]) -> str:
        """Configure multiple displays
        
        config = {
            "HDMI-1": {"mode": "1920x1080", "pos": "0x0", "rotate": "normal"},
            "eDP-1": {"mode": "1920x1080", "pos": "1920x0", "rotate": "normal", "primary": true}
        }
        """
        try:
            cmd = ["xrandr"]
            
            for display, settings in config.items():
                cmd.extend(["--output", display])
                
                if settings.get("off"):
                    cmd.append("--off")
                    continue
                
                if "mode" in settings:
                    cmd.extend(["--mode", settings["mode"]])
                
                if "pos" in settings:
                    cmd.extend(["--pos", settings["pos"]])
                
                if "rotate" in settings:
                    cmd.extend(["--rotate", settings["rotate"]])
                
                if settings.get("primary"):
                    cmd.append("--primary")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return "Display configuration applied"
            return f"Failed: {result.stderr}"
        except Exception as e:
            return f"Failed to configure displays: {str(e)}"
    
    # ==================== Other Settings ====================
    
    def set_keyboard_layout(self, layout: str, variant: str = "") -> str:
        """Set keyboard layout"""
        try:
            cmd = ["setxkbmap", layout]
            if variant:
                cmd.extend(["-variant", variant])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Keyboard layout set to {layout}"
            return f"Failed: {result.stderr}"
        except Exception as e:
            return f"Failed to set keyboard layout: {str(e)}"
    
    def get_keyboard_layout(self) -> str:
        """Get current keyboard layout"""
        try:
            result = subprocess.run(
                ["setxkbmap", "-query"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'layout' in line:
                        return f"Keyboard layout: {line.split(':')[1].strip()}"
            
            return "Could not determine keyboard layout"
        except Exception as e:
            return f"Failed to get keyboard layout: {str(e)}"
    
    def set_wallpaper(self, image_path: str, mode: str = "fill") -> str:
        """Set desktop wallpaper (GNOME)"""
        try:
            # Resolve path
            path = Path(image_path).expanduser().resolve()
            
            if not path.exists():
                return f"Image not found: {path}"
            
            # GNOME
            uri = f"file://{path}"
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri], check=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-options", mode], check=True)
            
            return f"Wallpaper set to {path}"
        except Exception as e:
            return f"Failed to set wallpaper: {str(e)}"
    
    def set_theme(self, theme: str, variant: str = "") -> str:
        """Set GTK theme (GNOME)"""
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme], check=True)
            
            if variant:
                subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", variant], check=True)
            
            return f"Theme set to {theme}"
        except Exception as e:
            return f"Failed to set theme: {str(e)}"
    
    def test(self) -> bool:
        """Test system settings"""
        try:
            # Test brightness
            self.get_brightness()
            
            # Test volume
            self.get_volume()
            
            # Test resolution
            self.get_resolution()
            
            logger.info("System settings test passed")
            return True
        except Exception as e:
            logger.error(f"System settings test failed: {e}")
            return False