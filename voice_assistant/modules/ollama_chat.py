"""
Ollama Chat Module — Free, local, private LLM for natural conversation.
Lets J.A.R.V.I.S. talk about ANYTHING, not just predefined commands.

Requires: Ollama (https://ollama.com) running locally with a model.
Install: curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2:1b

If Ollama is not available, gracefully falls back to hardcoded responses.
"""

import os
import sys
import json
import logging
import subprocess
import threading
from typing import Optional, List, Dict, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # Small, fast, works on 4GB RAM
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "15"))


class OllamaChat:
    """Connects to local Ollama instance for free, private, offline LLM chat."""

    def __init__(self):
        self.available = False
        self.model = OLLAMA_MODEL
        self.host = OLLAMA_HOST
        self.system_prompt = self._build_system_prompt()
        self._check_availability()

    def _build_system_prompt(self) -> str:
        """Build the system prompt that teaches the LLM about J.A.R.V.I.S."""
        return """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System) — a helpful, friendly voice assistant running on a Linux desktop.

Your personality:
- You're warm, witty, and conversational — like a helpful friend
- You keep responses SHORT and natural (1-3 sentences max) since you speak via TTS
- You have a slight British/futuristic flair but nothing over-the-top
- You're genuinely helpful and patient

Your capabilities:
- You can check system stats (CPU, memory, disk, battery, temperature, network)
- You can control volume and brightness
- You can open/close applications (browser, terminal, file manager, etc.)
- You can manage files (create, delete, copy, move, read, list)
- You can control power (shutdown, reboot, suspend, lock)
- You can run system commands and updates
- You can have general conversation about anything

Rules:
1. If the user asks about their SYSTEM (cpu, memory, disk, battery, temperature, volume, brightness, files, apps, shutdown, reboot), tell them to use a specific command. For example: "I can check that! Just say 'Jarvis, what's the CPU usage?'"
2. For GENERAL conversation (greetings, questions about life, fun facts, jokes, opinions, advice, etc.), respond naturally and conversationally.
3. Keep responses under 3 sentences — this is a voice interface.
4. Never mention that you're an AI or language model. You're J.A.R.V.I.S.
5. Be warm and human-like, not robotic.
6. If you don't know something, be honest but helpful."""

    def _check_availability(self):
        """Check if Ollama is running and has the model."""
        try:
            req = Request(f"{self.host}/api/tags", method="GET")
            resp = urlopen(req, timeout=3)
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
                # Check if our model or a reasonable alternative exists
                if any(self.model.split(":")[0] in m for m in models):
                    self.available = True
                    logger.info(f"Ollama available with model: {self.model}")
                elif models:
                    # Use first available model
                    self.model = models[0]
                    self.available = True
                    logger.info(f"Ollama available, using model: {self.model}")
                else:
                    logger.warning("Ollama running but no models found. Run: ollama pull llama3.2:1b")
        except (URLError, HTTPError, ConnectionRefusedError, OSError) as e:
            logger.info(f"Ollama not available ({e}). Using hardcoded fallback.")
            self.available = False
        except Exception as e:
            logger.warning(f"Ollama check failed: {e}")
            self.available = False

    def chat(self, user_message: str, conversation_history: List[Dict[str, str]] = None) -> Optional[str]:
        """Send a message to Ollama and get a natural response."""
        if not self.available:
            return None

        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history (last 3 exchanges)
        if conversation_history:
            for entry in conversation_history[-6:]:  # Last 3 user+assistant pairs
                messages.append(entry)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150,  # Keep responses short
            }
        }).encode()

        try:
            req = Request(
                f"{self.host}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urlopen(req, timeout=OLLAMA_TIMEOUT)
            result = json.loads(resp.read().decode())
            response = result.get("message", {}).get("content", "").strip()

            if response:
                # Clean up any markdown or quotes
                response = response.strip('"').strip("'")
                logger.info(f"Ollama response: {response[:100]}...")
                return response

        except HTTPError as e:
            logger.warning(f"Ollama HTTP error: {e.code} {e.reason}")
        except Exception as e:
            logger.warning(f"Ollama chat error: {e}")

        return None

    def stream_chat(self, user_message: str, conversation_history: List[Dict[str, str]] = None):
        """Stream response from Ollama (for future streaming support)."""
        if not self.available:
            return

        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            for entry in conversation_history[-6:]:
                messages.append(entry)
        messages.append({"role": "user", "content": user_message})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.7, "num_predict": 150}
        }).encode()

        try:
            req = Request(
                f"{self.host}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urlopen(req, timeout=OLLAMA_TIMEOUT * 2)
            buffer = ""
            for line in resp:
                if line:
                    try:
                        chunk = json.loads(line.decode())
                        if "message" in chunk and "content" in chunk["message"]:
                            buffer += chunk["message"]["content"]
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue
            if buffer:
                yield buffer
        except Exception as e:
            logger.warning(f"Ollama stream error: {e}")

    @staticmethod
    def install_instructions() -> str:
        """Return instructions for installing Ollama."""
        return (
            "To enable unlimited conversation, install Ollama (free, local, offline):\n"
            "  curl -fsSL https://ollama.com/install.sh | sh\n"
            "  ollama pull llama3.2:1b\n"
            "Then restart J.A.R.V.I.S."
        )
