"""
ai_helper.py - Gemini AI se baat karne ka shared helper.

Har AI tool isi file se Gemini ko call karega.
API key code mein nahi hoti, Render ke Environment Variable (GEMINI_API_KEY) se aati hai.
"""

import os
import time
import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Model ka naam Render mein GEMINI_MODEL se badla ja sakta hai (code badalne ki zaroorat nahi).
DEFAULT_MODEL = "gemini-3.5-flash-lite"


class AIError(Exception):
    """AI call fail hui. message user ko dikhane ke liye safe hai."""

    def __init__(self, message, status=500):
        super().__init__(message)
        self.message = message
        self.status = status


# ---------- Simple rate limit (free key ki limit bachane ke liye) ----------
_hits = {}
MAX_REQUESTS = 8      # itni requests
WINDOW_SECONDS = 60   # is time mein (har visitor ke liye)


def check_rate_limit(ip):
    """Agar visitor ne limit cross kar li to AIError uthata hai."""
    now = time.time()
    recent = [t for t in _hits.get(ip, []) if now - t < WINDOW_SECONDS]
    if len(recent) >= MAX_REQUESTS:
        raise AIError("You are sending requests too fast. Please wait a minute and try again.", 429)
    recent.append(now)
    _hits[ip] = recent

    # purane records saaf karte rahein taake memory na bhare
    if len(_hits) > 5000:
        for key in list(_hits.keys()):
            if not any(now - t < WINDOW_SECONDS for t in _hits[key]):
                _hits.pop(key, None)


def get_client_ip(request):
    """Render proxy ke peeche asli visitor ka IP."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def ask_gemini(prompt, system=None, temperature=0.8, max_tokens=4096):
    """Gemini se jawab leta hai aur plain text wapas karta hai."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    if not api_key:
        print("[AI] GEMINI_API_KEY Render ke Environment mein set nahi hai.")
        raise AIError("The AI service is not configured yet. Please try again later.", 503)

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    try:
        response = requests.post(
            GEMINI_URL.format(model=model),
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=body,
            timeout=60,
        )
    except requests.exceptions.Timeout:
        print("[AI] Gemini ne waqt par jawab nahi diya (timeout).")
        raise AIError("The AI took too long to respond. Please try again.", 504)
    except requests.exceptions.RequestException as e:
        print(f"[AI] Network error: {e}")
        raise AIError("Could not reach the AI service. Please try again.", 502)

    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message", response.text[:300])
        except ValueError:
            detail = response.text[:300]
        # Asli wajah Render ke Logs mein dikhegi
        print(f"[AI] Gemini error {response.status_code} (model={model}): {detail}")

        if response.status_code == 429:
            raise AIError("The AI is very busy right now. Please try again in a minute.", 429)
        if response.status_code == 404:
            raise AIError("The AI model is not available. Please try again later.", 503)
        if response.status_code in (400, 401, 403):
            raise AIError("The AI service rejected the request. Please try again later.", 503)
        raise AIError("The AI service had a problem. Please try again.", 502)

    try:
        data = response.json()
    except ValueError:
        raise AIError("The AI sent an unreadable answer. Please try again.", 502)

    candidates = data.get("candidates") or []
    if not candidates:
        print(f"[AI] Koi candidate nahi mila. promptFeedback={data.get('promptFeedback')}")
        raise AIError("The AI could not answer this topic. Please try a different one.", 422)

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()

    if not text:
        print(f"[AI] Khali jawab. finishReason={candidates[0].get('finishReason')}")
        raise AIError("The AI returned an empty answer. Please try again.", 502)

    return text