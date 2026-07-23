"""
Speech Recognition Module
Supports multiple engines: Google, Vosk, Sphinx, Whisper
"""

import os
import logging
import speech_recognition as sr
from typing import Optional, Callable
import threading
import time

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Handles speech recognition using various engines"""
    
    def __init__(self, engine: str = "google", language: str = "en-US", timeout: int = 5):
        self.engine = engine
        self.language = language
        self.timeout = timeout
        self.phrase_time_limit = 10
        self.energy_threshold = 300
        self.dynamic_energy_threshold = True
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = self.energy_threshold
        self.recognizer.dynamic_energy_threshold = self.dynamic_energy_threshold
        self.recognizer.pause_threshold = 0.8
        
        self.microphone = None
        try:
            self.microphone = sr.Microphone()
            self._calibrate_microphone()
        except Exception as e:
            logger.warning(f"Microphone initialization failed (PyAudio may be missing or no microphone connected): {e}")
        
        logger.info(f"Speech recognizer initialized with engine: {engine}")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            logger.warning(f"Microphone calibration failed: {e}")
    
    def listen(self, timeout: Optional[int] = None, phrase_time_limit: Optional[int] = None) -> Optional[str]:
        """Listen for speech and return recognized text"""
        timeout = timeout or self.timeout
        phrase_time_limit = phrase_time_limit or self.phrase_time_limit
        
        if not self.microphone:
            try:
                import sys
                import select
                print("\n[No microphone] Enter command manually: ", end="", flush=True)
                r, _, _ = select.select([sys.stdin], [], [], timeout or 5)
                if r:
                    line = sys.stdin.readline().strip()
                    if line:
                        logger.info(f"Terminal input: {line}")
                        return line.lower().strip()
                return None
            except Exception as e:
                logger.error(f"Fallback terminal input error: {e}")
                return None
        
        try:
            with self.microphone as source:
                logger.debug("Listening for speech...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            logger.debug("Processing audio...")
            text = self._recognize_audio(audio)
            
            if text:
                logger.info(f"Recognized: {text}")
                return text.lower().strip()
            
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout - no speech detected")
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
        
        return None
    
    def _recognize_audio(self, audio: sr.AudioData) -> Optional[str]:
        """Recognize audio using selected engine"""
        try:
            if self.engine == "google":
                return self.recognizer.recognize_google(audio, language=self.language)
            elif self.engine == "sphinx":
                return self.recognizer.recognize_sphinx(audio, language=self.language)
            elif self.engine == "vosk":
                return self._recognize_vosk(audio)
            elif self.engine == "whisper":
                return self._recognize_whisper(audio)
            else:
                logger.error(f"Unknown engine: {self.engine}")
                return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return None
    
    def _recognize_vosk(self, audio: sr.AudioData) -> Optional[str]:
        """Recognize using Vosk (offline)"""
        try:
            import vosk
            import json
            
            model_path = os.getenv("VOSK_MODEL_PATH", "/usr/share/vosk/model")
            if not os.path.exists(model_path):
                logger.error(f"Vosk model not found at {model_path}")
                return None
            
            model = vosk.Model(model_path)
            rec = vosk.KaldiRecognizer(model, 16000)
            
            audio_data = audio.get_wav_data(convert_rate=16000, convert_width=2)
            if rec.AcceptWaveform(audio_data):
                result = json.loads(rec.Result())
                return result.get("text", "")
            return None
        except ImportError:
            logger.error("Vosk not installed. Install with: pip install vosk")
            return None
        except Exception as e:
            logger.error(f"Vosk recognition error: {e}")
            return None
    
    def _recognize_whisper(self, audio: sr.AudioData) -> Optional[str]:
        """Recognize using Whisper (offline)"""
        try:
            import whisper
            import tempfile
            
            model_size = os.getenv("WHISPER_MODEL", "base")
            model = whisper.load_model(model_size)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio.get_wav_data())
                temp_path = f.name
            
            result = model.transcribe(temp_path, language=self.language.split('-')[0])
            os.unlink(temp_path)
            
            return result.get("text", "").strip()
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Whisper recognition error: {e}")
            return None
    
    def listen_for_wake_word(self, wake_word: str = "assistant", 
                            callback: Optional[Callable] = None) -> Optional[str]:
        """Listen continuously for wake word"""
        logger.info(f"Listening for wake word: '{wake_word}'")
        
        while True:
            text = self.listen(timeout=1, phrase_time_limit=3)
            if text and wake_word.lower() in text.lower():
                logger.info(f"Wake word detected: {text}")
                if callback:
                    callback()
                return text
            time.sleep(0.1)
    
    def listen_continuous(self, callback: Callable[[str], None], 
                         stop_event: threading.Event):
        """Continuous listening with callback for each recognized phrase"""
        logger.info("Starting continuous listening...")
        
        while not stop_event.is_set():
            text = self.listen(timeout=1, phrase_time_limit=5)
            if text:
                callback(text)
            time.sleep(0.1)
    
    def test(self) -> bool:
        """Test speech recognition"""
        try:
            logger.info("Testing speech recognition... Say something!")
            text = self.listen(timeout=5, phrase_time_limit=5)
            if text:
                logger.info(f"Test successful: '{text}'")
                return True
            else:
                logger.warning("Test failed: No speech recognized")
                return False
        except Exception as e:
            logger.error(f"Test error: {e}")
            return False
    
    def set_engine(self, engine: str):
        """Change recognition engine"""
        self.engine = engine
        logger.info(f"Speech engine changed to: {engine}")
    
    def set_language(self, language: str):
        """Change recognition language"""
        self.language = language
        logger.info(f"Speech language changed to: {language}")
    
    def adjust_sensitivity(self, energy_threshold: int = None):
        """Adjust microphone sensitivity"""
        if energy_threshold:
            self.recognizer.energy_threshold = energy_threshold
            self.recognizer.dynamic_energy_threshold = False
        else:
            self._calibrate_microphone()
        logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")


class WakeWordDetector:
    """Dedicated wake word detection using Porcupine or simple keyword matching"""
    
    def __init__(self, wake_words: list = None, sensitivity: float = 0.5):
        self.wake_words = wake_words or ["assistant", "hey assistant", "okay assistant"]
        self.sensitivity = sensitivity
        self.porcupine = None
        self._init_porcupine()
    
    def _init_porcupine(self):
        """Initialize Porcupine wake word engine if available"""
        try:
            import pvporcupine
            access_key = os.getenv("PORCUPINE_ACCESS_KEY")
            if access_key:
                self.porcupine = pvporcupine.create(
                    access_key=access_key,
                    keywords=self.wake_words,
                    sensitivities=[self.sensitivity] * len(self.wake_words)
                )
                logger.info("Porcupine wake word detector initialized")
        except ImportError:
            logger.info("Porcupine not available, using keyword matching")
        except Exception as e:
            logger.warning(f"Porcupine initialization failed: {e}")
    
    def detect(self, audio_data: bytes) -> int:
        """Detect wake word in audio data. Returns index of detected keyword or -1"""
        if self.porcupine:
            try:
                import struct
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, audio_data)
                return self.porcupine.process(pcm)
            except Exception as e:
                logger.error(f"Porcupine detection error: {e}")
                return -1
        return -1
    
    def cleanup(self):
        """Clean up resources"""
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None