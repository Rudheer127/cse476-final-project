import os 
import time
import random
import threading
import requests

API_KEY = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")
MODEL = os.getenv("MODEL_NAME", "bens_model")

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 30

# Global semaphore to limit concurrent API calls
MAX_CONCURRENT_API_CALLS = 3
_api_semaphore = threading.Semaphore(MAX_CONCURRENT_API_CALLS)

# Jitter range (seconds)
JITTER_MIN = 0.3
JITTER_MAX = 1.0

def call_model(prompt: str,
               system: str = "",
               model: str = MODEL,
               temperature: float = 0.0,
               timeout: int = 30,
               max_tokens: int = 256) -> dict:

    url = f"{API_BASE}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "echo": False,
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Add jitter before each attempt
            jitter = random.uniform(JITTER_MIN, JITTER_MAX)
            time.sleep(jitter)
            
            if attempt > 0:
                # Exponential backoff with jitter
                backoff = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
                extra_jitter = random.uniform(0, backoff * 0.3)
                time.sleep(backoff + extra_jitter)
            
            # Acquire semaphore before making API call
            with _api_semaphore:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            status = resp.status_code
            hdrs = dict(resp.headers)

            if status == 200:
                data = resp.json()
                text = data.get("choices", [{}])[0].get("text", "").strip()
                return {"ok": True, "text": text, "raw": data, "status": status, "error": None, "headers": hdrs}

            # Check for rate limit error - retry
            try:
                err_data = resp.json()
                err_text = str(err_data)
                if "rate_limit" in err_text.lower() or "too many" in err_text.lower():
                    last_error = err_text
                    continue
            except Exception:
                err_text = resp.text

            # Non-rate-limit error
            return {"ok": False, "text": None, "raw": None, "status": status, "error": err_text, "headers": hdrs}

        except requests.RequestException as e:
            last_error = str(e)
            continue

    # All retries exhausted
    return {"ok": False, "text": "", "raw": None, "status": -1, "error": f"Max retries exceeded: {last_error}", "headers": {}}
