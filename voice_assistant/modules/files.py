"""
File System Manager Module
Handles file and directory operations: create, delete, copy, move, rename, list, search, read
"""

import os
import logging
import shutil
import glob
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
import subprocess

logger = logging.getLogger(__name__)


class FileSystemManager:
    """Manages file system operations"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.home()
        self.current_path = self.base_path
        logger.info(f"FileSystemManager initialized with base path: {self.base_path}")
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute path"""
        if not path:
            return self.current_path
        
        path = path.strip()
        path = path.replace("~", str(Path.home()))
        
        # Handle relative paths
        p = Path(path)
        if p.is_absolute():
            return p
        else:
            return (self.current_path / p).resolve()
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    
    def create_file(self, path: str, content: str = "") -> str:
        """Create a file with optional content"""
        try:
            filepath = self._resolve_path(path)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Created file: {filepath}")
            return f"File created: {filepath}"
        except Exception as e:
            logger.error(f"Create file error: {e}")
            return f"Failed to create file: {str(e)}"
    
    def create_directory(self, path: str) -> str:
        """Create a directory"""
        try:
            dirpath = self._resolve_path(path)
            dirpath.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created directory: {dirpath}")
            return f"Directory created: {dirpath}"
        except Exception as e:
            logger.error(f"Create directory error: {e}")
            return f"Failed to create directory: {str(e)}"
    
    def delete_file(self, path: str, force: bool = False) -> str:
        """Delete a file"""
        try:
            filepath = self._resolve_path(path)
            
            if not filepath.exists():
                return f"File not found: {filepath}"
            
            if filepath.is_dir():
                return f"Path is a directory, use delete_directory: {filepath}"
            
            # Confirm if not forced (in real usage, this would be handled by UI)
            if not force:
                return f"Confirm deletion of {filepath.name}? Use force=true to confirm."
            
            filepath.unlink()
            logger.info(f"Deleted file: {filepath}")
            return f"File deleted: {filepath}"
        except Exception as e:
            logger.error(f"Delete file error: {e}")
            return f"Failed to delete file: {str(e)}"
    
    def delete_directory(self, path: str, recursive: bool = False, force: bool = False) -> str:
        """Delete a directory"""
        try:
            dirpath = self._resolve_path(path)
            
            if not dirpath.exists():
                return f"Directory not found: {dirpath}"
            
            if not dirpath.is_dir():
                return f"Path is not a directory: {dirpath}"
            
            if not force:
                return f"Confirm deletion of {dirpath.name}? Use force=true to confirm."
            
            if recursive:
                shutil.rmtree(dirpath)
            else:
                # Only delete if empty
                if any(dirpath.iterdir()):
                    return f"Directory not empty. Use recursive=true to delete anyway."
                dirpath.rmdir()
            
            logger.info(f"Deleted directory: {dirpath}")
            return f"Directory deleted: {dirpath}"
        except Exception as e:
            logger.error(f"Delete directory error: {e}")
            return f"Failed to delete directory: {str(e)}"
    
    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> str:
        """Copy a file"""
        try:
            src = self._resolve_path(source)
            dst = self._resolve_path(destination)
            
            if not src.exists():
                return f"Source not found: {src}"
            
            if src.is_dir():
                return f"Source is a directory. Use copy_directory for directories."
            
            if dst.exists() and not overwrite:
                return f"Destination exists. Use overwrite=true to replace."
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            
            logger.info(f"Copied {src} to {dst}")
            return f"File copied: {src} -> {dst}"
        except Exception as e:
            logger.error(f"Copy file error: {e}")
            return f"Failed to copy file: {str(e)}"
    
    def copy_directory(self, source: str, destination: str, overwrite: bool = False) -> str:
        """Copy a directory"""
        try:
            src = self._resolve_path(source)
            dst = self._resolve_path(destination)
            
            if not src.exists():
                return f"Source not found: {src}"
            
            if not src.is_dir():
                return f"Source is not a directory: {src}"
            
            if dst.exists():
                if not overwrite:
                    return f"Destination exists. Use overwrite=true to replace."
                shutil.rmtree(dst)
            
            shutil.copytree(src, dst)
            
            logger.info(f"Copied directory {src} to {dst}")
            return f"Directory copied: {src} -> {dst}"
        except Exception as e:
            logger.error(f"Copy directory error: {e}")
            return f"Failed to copy directory: {str(e)}"
    
    def move_file(self, source: str, destination: str, overwrite: bool = False) -> str:
        """Move/rename a file or directory"""
        try:
            src = self._resolve_path(source)
            dst = self._resolve_path(destination)
            
            if not src.exists():
                return f"Source not found: {src}"
            
            if dst.exists() and not overwrite:
                return f"Destination exists. Use overwrite=true to replace."
            
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            
            logger.info(f"Moved {src} to {dst}")
            return f"Moved: {src} -> {dst}"
        except Exception as e:
            logger.error(f"Move error: {e}")
            return f"Failed to move: {str(e)}"
    
    def rename_file(self, path: str, new_name: str) -> str:
        """Rename a file or directory"""
        try:
            filepath = self._resolve_path(path)
            
            if not filepath.exists():
                return f"File not found: {filepath}"
            
            new_path = filepath.parent / new_name
            
            if new_path.exists():
                return f"Name already exists: {new_name}"
            
            filepath.rename(new_path)
            
            logger.info(f"Renamed {filepath} to {new_path}")
            return f"Renamed: {filepath.name} -> {new_name}"
        except Exception as e:
            logger.error(f"Rename error: {e}")
            return f"Failed to rename: {str(e)}"
    
    def list_directory(self, path: str = "", show_hidden: bool = False, 
                       detailed: bool = False) -> str:
        """List directory contents"""
        try:
            dirpath = self._resolve_path(path)
            
            if not dirpath.exists():
                return f"Directory not found: {dirpath}"
            
            if not dirpath.is_dir():
                return f"Path is not a directory: {dirpath}"
            
            items = []
            for item in sorted(dirpath.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                if detailed:
                    stat = item.stat()
                    items.append({
                        "name": item.name + ("/" if item.is_dir() else ""),
                        "size": self._format_size(stat.st_size) if item.is_file() else "-",
                        "modified": self._format_time(stat.st_mtime),
                        "permissions": oct(stat.st_mode)[-3:],
                        "type": "directory" if item.is_dir() else "file"
                    })
                else:
                    items.append(item.name + ("/" if item.is_dir() else ""))
            
            self.current_path = dirpath
            
            if detailed:
                lines = [f"Contents of {dirpath}:"] 
                lines.append(f"{'Name':<40} {'Size':>10} {'Modified':<20} {'Perm':>5} {'Type'}")
                lines.append("-" * 85)
                for item in items:
                    lines.append(f"{item['name']:<40} {item['size']:>10} {item['modified']:<20} {item['permissions']:>5} {item['type']}")
                return "\n".join(lines)
            else:
                if not items:
                    return f"Directory empty: {dirpath}"
                return f"Contents of {dirpath}:\n" + "\n".join(items)
        except Exception as e:
            logger.error(f"List directory error: {e}")
            return f"Failed to list directory: {str(e)}"
    
    def search_files(self, pattern: str, path: str = "", 
                     recursive: bool = True, max_results: int = 50) -> str:
        """Search for files matching pattern"""
        try:
            search_path = self._resolve_path(path)
            
            if not search_path.exists():
                return f"Search path not found: {search_path}"
            
            results = []
            
            if recursive:
                for filepath in search_path.rglob("*"):
                    if fnmatch.fnmatch(filepath.name, pattern):
                        results.append(filepath)
                        if len(results) >= max_results:
                            break
            else:
                for filepath in search_path.iterdir():
                    if fnmatch.fnmatch(filepath.name, pattern):
                        results.append(filepath)
                        if len(results) >= max_results:
                            break
            
            if not results:
                return f"No files found matching '{pattern}' in {search_path}"
            
            lines = [f"Found {len(results)} file(s) matching '{pattern}':"]
            for f in results:
                rel = f.relative_to(search_path)
                size = self._format_size(f.stat().st_size) if f.is_file() else "-"
                lines.append(f"  {rel} ({size})")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Search failed: {str(e)}"
    
    def read_file(self, path: str, max_lines: int = 100) -> str:
        """Read file contents"""
        try:
            filepath = self._resolve_path(path)
            
            if not filepath.exists():
                return f"File not found: {filepath}"
            
            if filepath.is_dir():
                return f"Path is a directory: {filepath}"
            
            # Check file size
            size = filepath.stat().st_size
            if size > 10 * 1024 * 1024:  # 10MB limit
                return f"File too large ({self._format_size(size)}). Use cat/less for large files."
            
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            if len(lines) > max_lines:
                content = "".join(lines[:max_lines])
                content += f"\n... ({len(lines) - max_lines} more lines truncated)"
            else:
                content = "".join(lines)
            
            return f"Contents of {filepath}:\n{content}"
        except UnicodeDecodeError:
            return f"File appears to be binary: {filepath}"
        except Exception as e:
            logger.error(f"Read file error: {e}")
            return f"Failed to read file: {str(e)}"
    
    def write_file(self, path: str, content: str, append: bool = False) -> str:
        """Write content to file"""
        try:
            filepath = self._resolve_path(path)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(filepath, mode) as f:
                f.write(content)
            
            action = "Appended to" if append else "Wrote to"
            logger.info(f"{action} file: {filepath}")
            return f"{action} file: {filepath}"
        except Exception as e:
            logger.error(f"Write file error: {e}")
            return f"Failed to write file: {str(e)}"
    
    def get_file_info(self, path: str) -> str:
        """Get detailed file information"""
        try:
            filepath = self._resolve_path(path)
            
            if not filepath.exists():
                return f"Path not found: {filepath}"
            
            stat = filepath.stat()
            
            info = [
                f"Path: {filepath}",
                f"Name: {filepath.name}",
                f"Type: {'Directory' if filepath.is_dir() else 'File' if filepath.is_file() else 'Other'}",
                f"Size: {self._format_size(stat.st_size)} ({stat.st_size} bytes)",
                f"Permissions: {oct(stat.st_mode)[-3:]} ({oct(stat.st_mode)})",
                f"Owner: {stat.st_uid}",
                f"Group: {stat.st_gid}",
                f"Created: {self._format_time(stat.st_ctime)}",
                f"Modified: {self._format_time(stat.st_mtime)}",
                f"Accessed: {self._format_time(stat.st_atime)}",
            ]
            
            if filepath.is_file():
                # Get MIME type
                import mimetypes
                mime, _ = mimetypes.guess_type(str(filepath))
                info.append(f"MIME Type: {mime or 'Unknown'}")
                
                # Check if text file
                try:
                    with open(filepath, 'r') as f:
                        f.read(1024)
                    info.append("Content: Text")
                except:
                    info.append("Content: Binary")
            
            return "\n".join(info)
        except Exception as e:
            logger.error(f"Get file info error: {e}")
            return f"Failed to get file info: {str(e)}"
    
    def change_directory(self, path: str) -> str:
        """Change current working directory"""
        try:
            dirpath = self._resolve_path(path)
            
            if not dirpath.exists():
                return f"Directory not found: {dirpath}"
            
            if not dirpath.is_dir():
                return f"Path is not a directory: {dirpath}"
            
            self.current_path = dirpath
            return f"Changed directory to: {dirpath}"
        except Exception as e:
            logger.error(f"Change directory error: {e}")
            return f"Failed to change directory: {str(e)}"
    
    def get_current_directory(self) -> str:
        """Get current working directory"""
        return f"Current directory: {self.current_path}"
    
    def get_disk_usage(self, path: str = "") -> str:
        """Get disk usage for path"""
        try:
            target = self._resolve_path(path) if path else Path("/")
            
            usage = shutil.disk_usage(target)
            
            total = self._format_size(usage.total)
            used = self._format_size(usage.used)
            free = self._format_size(usage.free)
            percent = (usage.used / usage.total) * 100
            
            return (
                f"Disk Usage for {target}:\n"
                f"  Total: {total}\n"
                f"  Used:  {used} ({percent:.1f}%)\n"
                f"  Free:  {free}"
            )
        except Exception as e:
            logger.error(f"Disk usage error: {e}")
            return f"Failed to get disk usage: {str(e)}"
    
    def find_large_files(self, path: str = "", min_size_mb: int = 100, 
                         max_results: int = 20) -> str:
        """Find large files"""
        try:
            search_path = self._resolve_path(path)
            min_size = min_size_mb * 1024 * 1024
            
            large_files = []
            for filepath in search_path.rglob("*"):
                if filepath.is_file():
                    try:
                        size = filepath.stat().st_size
                        if size >= min_size:
                            large_files.append((filepath, size))
                    except:
                        continue
            
            large_files.sort(key=lambda x: x[1], reverse=True)
            
            if not large_files:
                return f"No files larger than {min_size_mb}MB found in {search_path}"
            
            lines = [f"Large files (> {min_size_mb}MB) in {search_path}:"]
            for filepath, size in large_files[:max_results]:
                rel = filepath.relative_to(search_path)
                lines.append(f"  {rel}: {self._format_size(size)}")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Find large files error: {e}")
            return f"Search failed: {str(e)}"
    
    def test(self) -> bool:
        """Test file system operations"""
        try:
            # Test basic operations
            test_dir = self.base_path / ".voice_assistant_test"
            test_dir.mkdir(exist_ok=True)
            
            test_file = test_dir / "test.txt"
            test_file.write_text("test content")
            
            assert test_file.read_text() == "test content"
            
            test_file.unlink()
            test_dir.rmdir()
            
            logger.info("File system test passed")
            return True
        except Exception as e:
            logger.error(f"File system test failed: {e}")
            return False