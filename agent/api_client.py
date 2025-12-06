import os 
import requests

API_KEY = os.getenv("OPENAI_API_KEY", "cse476")
API_BASE = os.getenv("API_BASE", "http://10.4.58.53:41701/v1")
MODEL = os.getenv("MODEL_NAME", "bens_model")

def call_model(prompt: str,
               system: str = "",
               model: str = MODEL,
               temperature: float = 0.0,
               timeout: int = 30,
               max_tokens: int = 1024) -> dict:

    url = f"{API_BASE}/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }

    payload = {
        "model": model,
        "prompt": prompt
    }

    try:
        print("Calling model...")
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        print("Model returned.")
        status = resp.status_code
        hdrs   = dict(resp.headers)

        if status == 200:
            data = resp.json()

            text = data.get("choices", [{}])[0].get("text", "").strip()

            return {"ok": True, "text": text, "raw": data, "status": status, "error": None, "headers": hdrs}

        else:
            try:
                err_text = resp.json()
            except Exception:
                err_text = resp.text

            return {"ok": False, "text": None, "raw": None, "status": status, "error": str(err_text), "headers": hdrs}

    except requests.RequestException as e:
        return {"ok": False, "text": "", "raw": None, "status": -1, "error": str(e), "headers": {}}
