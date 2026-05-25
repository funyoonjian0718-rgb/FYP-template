from __future__ import annotations

import time

import httpx

from app.core.settings import settings


class GenerationService:
    def generate(self, prompt: str) -> str:
        # Try /api/chat first (more reliable for llama3), fallback to /api/generate if needed
        base_url = settings.ollama_base_url.rstrip("/")
        url_chat = base_url + "/api/chat"
        url_generate = base_url + "/api/generate"

        # Retry loop for intermittent connection issues
        max_retries = 3
        backoff = 1.0
        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(timeout=120) as client:
                    chat_payload = {
                        "model": settings.ollama_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    }
                    r = client.post(url_chat, json=chat_payload)

                    # Success
                    if r.status_code == 200:
                        data = r.json()
                        return str(data.get("message", {}).get("content", "")).strip()

                    # If chat isn't supported (404), try generate
                    if r.status_code == 404:
                        payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
                        r2 = client.post(url_generate, json=payload)
                        if r2.status_code == 200:
                            data = r2.json()
                            return str(data.get("response", "")).strip()
                        else:
                            return f"Error: Both /api/chat and /api/generate failed. /api/generate returned {r2.status_code}"

                    # Server error -> provide diagnostics
                    if r.status_code >= 500:
                        return (
                            f"Error: Ollama returned {r.status_code}. This usually means:\n"
                            f"1. Model '{settings.ollama_model}' is not fully loaded\n"
                            f"2. Run in PowerShell: ollama list\n"
                            f"3. If model missing, run: ollama pull {settings.ollama_model}\n"
                            f"4. If stuck, restart Ollama\n"
                            f"Debug response: {r.text[:200]}"
                        )

                    return f"Error: Ollama API returned {r.status_code}: {r.text[:500]}"

            except (httpx.ConnectError, httpx.ReadError) as e:
                # Intermittent connection error — retry with backoff
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return (
                    "Error: Cannot connect to Ollama at {}.\n".format(settings.ollama_base_url)
                    + "Fixes:\n"
                    + "1. Ensure Ollama is installed from https://ollama.ai\n"
                    + "2. Start Ollama: ollama serve\n"
                    + "3. Pull model: ollama pull {}\n".format(settings.ollama_model)
                    + "4. Wait for download to complete"
                )
            except httpx.TimeoutException:
                # Timeout — model may be busy or too large
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return (
                    f"Error: Ollama request timed out (120 seconds).\n"
                    f"Model '{settings.ollama_model}' may be too large or busy.\n"
                    f"Try a smaller model: ollama pull phi (or mistral)"
                )
            except Exception as e:
                return f"Error: {type(e).__name__}: {str(e)}"


generation_service = GenerationService()

