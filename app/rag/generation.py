from __future__ import annotations

from typing import Any

import httpx

from app.core.settings import settings


class GenerationService:
    def generate(self, prompt: str) -> str:
        # Try /api/chat first (more reliable for llama3), fallback to /api/generate if needed
        base_url = settings.ollama_base_url.rstrip("/")
        try:
            with httpx.Client(timeout=120) as client:
                # Try /api/chat first (Ollama chat endpoint - most reliable)
                url_chat = base_url + "/api/chat"
                chat_payload = {"model": settings.ollama_model, "messages": [{"role": "user", "content": prompt}], "stream": False}
                r = client.post(url_chat, json=chat_payload)
                
                # If /api/chat works, use it
                if r.status_code == 200:
                    data = r.json()
                    return str(data.get("message", {}).get("content", "")).strip()
                
                # If /api/chat fails with 404, try /api/generate
                if r.status_code == 404:
                    url_generate = base_url + "/api/generate"
                    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
                    r2 = client.post(url_generate, json=payload)
                    if r2.status_code == 200:
                        data = r2.json()
                        return str(data.get("response", "")).strip()
                    else:
                        return f"Error: Both /api/chat and /api/generate failed. /api/generate returned {r2.status_code}"
                
                # If we get a 500 or other error, provide detailed diagnostics
                if r.status_code >= 500:
                    return (
                        f"Error: Ollama returned {r.status_code}. This usually means:\n"
                        f"1. Model '{settings.ollama_model}' is not fully loaded\n"
                        f"2. Run in PowerShell: ollama list\n"
                        f"3. If model missing, run: ollama pull {settings.ollama_model}\n"
                        f"4. If stuck, restart Ollama\n"
                        f"Debug response: {r.text[:200]}"
                    )
                
                # Other errors
                return f"Error: Ollama API returned {r.status_code}: {r.text[:500]}"
                
        except httpx.ConnectError:
            return (
                "Error: Cannot connect to Ollama at http://localhost:11434.\n"
                "Fixes:\n"
                "1. Ensure Ollama is installed from https://ollama.ai\n"
                "2. Start Ollama: ollama serve\n"
                "3. Pull model: ollama pull llama3\n"
                "4. Wait for download to complete"
            )
        except httpx.TimeoutException:
            return (
                f"Error: Ollama request timed out (120 seconds).\n"
                f"Model '{settings.ollama_model}' may be too large or busy.\n"
                f"Try a smaller model: ollama pull phi (or mistral)"
            )
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"


generation_service = GenerationService()

