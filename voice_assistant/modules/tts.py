"""
Text-to-Speech Module
Supports multiple engines: pyttsx3, gTTS, espeak, festival
"""

import os
import logging
import tempfile
import subprocess
import threading
from typing import Optional, List, Dict
import pyttsx3

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Handles text-to-speech synthesis using various engines"""
    
    def __init__(self, engine: str = "pyttsx3", rate: int = 180, volume: float = 1.0, voice: str = ""):
        self.engine_name = engine
        self.rate = rate
        self.volume = volume
        self.voice_id = voice
        self.engine = None
        self.voices = []
        self._lock = threading.Lock()
        
        self._init_engine()
        logger.info(f"TTS initialized with engine: {engine}, rate: {rate}, volume: {volume}")
    
    def _init_engine(self):
        """Initialize the selected TTS engine"""
        if self.engine_name == "pyttsx3":
            self._init_pyttsx3()
        elif self.engine_name == "gtts":
            self._init_gtts()
        elif self.engine_name == "espeak":
            self._init_espeak()
        elif self.engine_name == "festival":
            self._init_festival()
        else:
            logger.warning(f"Unknown TTS engine: {self.engine_name}, falling back to pyttsx3")
            self.engine_name = "pyttsx3"
            self._init_pyttsx3()
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            self.voices = self.engine.getProperty('voices')
            if self.voice_id:
                self.set_voice(self.voice_id)
            else:
                # Try to find a good default voice
                self._select_best_voice()
                
            logger.info("pyttsx3 engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.engine = None
    
    def _init_gtts(self):
        """Initialize gTTS (Google Text-to-Speech)"""
        try:
            import gtts
            self.gtts_lang = os.getenv("TTS_LANGUAGE", "en")
            logger.info("gTTS engine initialized")
        except ImportError:
            logger.error("gTTS not installed. Install with: pip install gtts")
            self.engine_name = "pyttsx3"
            self._init_pyttsx3()
    
    def _init_espeak(self):
        """Initialize eSpeak"""
        try:
            subprocess.run(["espeak", "--version"], capture_output=True, check=True)
            self.espeak_voice = os.getenv("ESPEAK_VOICE", "en")
            logger.info("eSpeak engine initialized")
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.error("eSpeak not found. Install with: sudo apt install espeak")
            self.engine_name = "pyttsx3"
            self._init_pyttsx3()
    
    def _init_festival(self):
        """Initialize Festival"""
        try:
            subprocess.run(["festival", "--version"], capture_output=True, check=True)
            logger.info("Festival engine initialized")
        except (FileNotFoundError, subprocess.CalledProcessError):
            logger.error("Festival not found. Install with: sudo apt install festival")
            self.engine_name = "pyttsx3"
            self._init_pyttsx3()
    
    def _select_best_voice(self):
        """Select the best available voice"""
        if not self.voices:
            return
        
        # Prefer English voices, then female voices
        preferred = [
            v for v in self.voices 
            if 'english' in v.name.lower() or 'en_' in v.id.lower()
        ]
        
        if preferred:
            female = [v for v in preferred if 'female' in v.name.lower() or 'zira' in v.id.lower()]
            if female:
                self.engine.setProperty('voice', female[0].id)
                logger.info(f"Selected voice: {female[0].name}")
            else:
                self.engine.setProperty('voice', preferred[0].id)
                logger.info(f"Selected voice: {preferred[0].name}")
    
    def speak(self, text: str, blocking: bool = True):
        """Speak the given text"""
        if not text or not text.strip():
            return
        
        text = text.strip()
        logger.debug(f"Speaking: {text[:100]}...")
        
        with self._lock:
            try:
                if self.engine_name == "pyttsx3":
                    self._speak_pyttsx3(text, blocking)
                elif self.engine_name == "gtts":
                    self._speak_gtts(text)
                elif self.engine_name == "espeak":
                    self._speak_espeak(text)
                elif self.engine_name == "festival":
                    self._speak_festival(text)
            except Exception as e:
                logger.error(f"TTS error: {e}")
                # Fallback to pyttsx3
                if self.engine_name != "pyttsx3":
                    self.engine_name = "pyttsx3"
                    self._init_pyttsx3()
                    self.speak(text, blocking)
    
    def _speak_pyttsx3(self, text: str, blocking: bool):
        """Speak using pyttsx3"""
        if not self.engine:
            self._init_pyttsx3()
        
        if self.engine:
            self.engine.say(text)
            if blocking:
                self.engine.runAndWait()
            else:
                self.engine.startLoop(False)
                # Note: For non-blocking, you'd need to manage the loop separately
    
    def _speak_gtts(self, text: str):
        """Speak using gTTS"""
        try:
            from gtts import gTTS
            import pygame
            
            tts = gTTS(text=text, lang=self.gtts_lang, slow=False)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_file = f.name
                tts.save(temp_file)
            
            # Play using pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            os.unlink(temp_file)
        except ImportError:
            logger.error("gTTS or pygame not installed")
            self._fallback_speak(text)
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            self._fallback_speak(text)
    
    def _speak_espeak(self, text: str):
        """Speak using eSpeak"""
        try:
            cmd = ["espeak", "-v", self.espeak_voice, "-s", str(self.rate), "-a", str(int(self.volume * 100)), text]
            subprocess.run(cmd, check=True)
        except Exception as e:
            logger.error(f"eSpeak error: {e}")
            self._fallback_speak(text)
    
    def _speak_festival(self, text: str):
        """Speak using Festival"""
        try:
            cmd = ["festival", "--tts"]
            subprocess.run(cmd, input=text.encode(), check=True)
        except Exception as e:
            logger.error(f"Festival error: {e}")
            self._fallback_speak(text)
    
    def _fallback_speak(self, text: str):
        """Fallback to pyttsx3"""
        if self.engine_name != "pyttsx3":
            self.engine_name = "pyttsx3"
            self._init_pyttsx3()
        self.speak(text)
    
    def speak_async(self, text: str):
        """Speak asynchronously (non-blocking)"""
        thread = threading.Thread(target=self.speak, args=(text, False))
        thread.daemon = True
        thread.start()
        return thread
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.rate = rate
        if self.engine_name == "pyttsx3" and self.engine:
            self.engine.setProperty('rate', rate)
        logger.info(f"Speech rate set to: {rate}")
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.engine_name == "pyttsx3" and self.engine:
            self.engine.setProperty('volume', self.volume)
        logger.info(f"Volume set to: {self.volume}")
    
    def set_voice(self, voice_id: str):
        """Set voice by ID"""
        if self.engine_name == "pyttsx3" and self.engine:
            for voice in self.voices:
                if voice_id in voice.id or voice_id in voice.name:
                    self.engine.setProperty('voice', voice.id)
                    self.voice_id = voice.id
                    logger.info(f"Voice set to: {voice.name}")
                    return True
        logger.warning(f"Voice not found: {voice_id}")
        return False
    
    def list_voices(self) -> List[Dict]:
        """List available voices"""
        voices_info = []
        if self.engine_name == "pyttsx3" and self.voices:
            for voice in self.voices:
                voices_info.append({
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                })
        return voices_info
    
    def save_to_file(self, text: str, filename: str):
        """Save speech to audio file"""
        try:
            if self.engine_name == "pyttsx3" and self.engine:
                self.engine.save_to_file(text, filename)
                self.engine.runAndWait()
                logger.info(f"Speech saved to: {filename}")
            elif self.engine_name == "gtts":
                from gtts import gTTS
                tts = gTTS(text=text, lang=self.gtts_lang)
                tts.save(filename)
                logger.info(f"Speech saved to: {filename}")
            else:
                logger.warning("Save to file only supported for pyttsx3 and gTTS")
        except Exception as e:
            logger.error(f"Save to file error: {e}")
    
    def test(self) -> bool:
        """Test TTS engine"""
        try:
            test_text = "Voice assistant test successful."
            logger.info("Testing TTS...")
            self.speak(test_text)
            return True
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            return False
    
    def stop(self):
        """Stop current speech"""
        if self.engine_name == "pyttsx3" and self.engine:
            self.engine.stop()
        elif self.engine_name == "gtts":
            try:
                import pygame
                pygame.mixer.music.stop()
            except:
                pass
        logger.info("TTS stopped")


class TTSManager:
    """High-level TTS manager with queue and priority support"""
    
    def __init__(self, tts: TextToSpeech):
        self.tts = tts
        self.queue = []
        self.processing = False
        self._lock = threading.Lock()
    
    def say(self, text: str, priority: int = 0):
        """Add text to speech queue"""
        with self._lock:
            self.queue.append((priority, text))
            self.queue.sort(key=lambda x: x[0], reverse=True)
        
        if not self.processing:
            self._process_queue()
    
    def _process_queue(self):
        """Process speech queue"""
        self.processing = True
        
        while True:
            with self._lock:
                if not self.queue:
                    self.processing = False
                    break
                _, text = self.queue.pop(0)
            
            self.tts.speak(text)
        
        self.processing = False
    
    def clear_queue(self):
        """Clear speech queue"""
        with self._lock:
            self.queue.clear()
        self.tts.stop()
    
    def wait_until_done(self):
        """Wait until queue is processed"""
        while self.processing or self.queue:
            import time
            time.sleep(0.1)