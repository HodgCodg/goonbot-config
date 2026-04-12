#!/usr/bin/env python3
"""
ChatGPT integration for GoonBot via OpenAI's ChatGPT web API.
Uses session token from a logged-in browser to access ChatGPT Plus.

Setup: Extract your session token from browser cookies:
  1. Log into chatgpt.com in your browser
  2. Open DevTools → Application → Cookies → chatgpt.com
  3. Copy the value of '__Secure-next-auth.session-token'
  4. Run: python3 chatgpt.py setup TOKEN_VALUE

Usage:
  python3 chatgpt.py setup TOKEN           # Save session token
  python3 chatgpt.py ask "prompt"           # Ask ChatGPT (default model)
  python3 chatgpt.py ask "prompt" --model gpt-4o  # Specify model
  python3 chatgpt.py status                 # Check if token is valid
  python3 chatgpt.py models                 # List available models
"""

import sys
import os
import json
import ssl
import http.cookiejar
import urllib.request
import urllib.error
import time
import uuid
import argparse

CONFIG_FILE = os.path.expanduser("~/.config/goonbot/chatgpt.json")
CHATGPT_BASE = "https://chatgpt.com"
BACKEND_API = f"{CHATGPT_BASE}/backend-api"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def get_access_token():
    """Get a fresh access token using the session token."""
    cfg = load_config()
    session_token = cfg.get("session_token")
    if not session_token:
        print("ERROR: No session token configured.")
        print("Run: python3 chatgpt.py setup YOUR_SESSION_TOKEN")
        print("Get it from browser DevTools → Cookies → __Secure-next-auth.session-token")
        sys.exit(1)

    # Check if we have a cached access token that's still fresh
    access_token = cfg.get("access_token")
    expires_at = cfg.get("expires_at", 0)
    if access_token and time.time() < expires_at - 60:
        return access_token

    # Refresh the access token using session token
    ssl_ctx = ssl.create_default_context()
    cookie_jar = http.cookiejar.CookieJar()

    # Create session cookie
    cookie = http.cookiejar.Cookie(
        version=0, name="__Secure-next-auth.session-token",
        value=session_token, port=None, port_specified=False,
        domain=".chatgpt.com", domain_specified=True, domain_initial_dot=True,
        path="/", path_specified=True, secure=True, expires=None,
        discard=True, comment=None, comment_url=None, rest={}, rfc2109=False
    )
    cookie_jar.set_cookie(cookie)

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=ssl_ctx)
    )

    req = urllib.request.Request(
        f"{CHATGPT_BASE}/api/auth/session",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
    )

    try:
        resp = opener.open(req, timeout=15)
        data = json.loads(resp.read().decode())
        access_token = data.get("accessToken")
        if not access_token:
            print("ERROR: Could not get access token. Session token may be expired.")
            print("Re-extract your session token from the browser and run setup again.")
            sys.exit(1)

        # Cache it (usually valid for ~1 hour)
        cfg["access_token"] = access_token
        cfg["expires_at"] = time.time() + 3500  # ~58 minutes
        save_config(cfg)
        return access_token
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300] if e.fp else ""
        print(f"ERROR: HTTP {e.code} refreshing token: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach ChatGPT: {e.reason}")
        sys.exit(1)


def api_request(method, path, data=None, stream=False):
    """Make an authenticated request to ChatGPT backend API."""
    token = get_access_token()
    ssl_ctx = ssl.create_default_context()

    url = f"{BACKEND_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/145.0.0.0 Safari/537.36",
        }
    )

    try:
        resp = urllib.request.urlopen(req, timeout=120, context=ssl_ctx)
        if stream:
            return resp  # Return raw response for streaming
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300] if e.fp else ""
        if e.code == 401:
            # Token expired, clear cache and retry
            cfg = load_config()
            cfg.pop("access_token", None)
            cfg.pop("expires_at", None)
            save_config(cfg)
            print("ERROR: Access token expired. Run the command again to auto-refresh.")
        else:
            print(f"ERROR: HTTP {e.code}: {body}")
        sys.exit(1)


def cmd_setup(token):
    """Save session token and verify it works."""
    cfg = load_config()
    cfg["session_token"] = token
    cfg.pop("access_token", None)
    cfg.pop("expires_at", None)
    save_config(cfg)

    # Try to get access token
    try:
        access_token = get_access_token()
        print(f"OK: Session token valid. Access token obtained.")
        print(f"Token cached for ~1 hour, auto-refreshes using session token.")
    except SystemExit:
        print("WARNING: Token saved but could not verify. It may be expired.")


def cmd_status():
    """Check if the current session is valid."""
    cfg = load_config()
    if not cfg.get("session_token"):
        print("NOT_SETUP: No session token configured. Run 'chatgpt.py setup TOKEN'")
        return
    try:
        token = get_access_token()
        # Try to get models to verify full access
        models = api_request("GET", "/models")
        model_list = [m.get("slug", m.get("id", "?")) for m in models.get("models", [])]
        print(f"LOGGED_IN: ChatGPT session active. Available models: {', '.join(model_list[:5])}")
    except SystemExit:
        print("EXPIRED: Session token may be expired. Re-extract from browser.")


def cmd_models():
    """List available models."""
    models = api_request("GET", "/models")
    for m in models.get("models", []):
        slug = m.get("slug", "?")
        title = m.get("title", slug)
        tags = m.get("tags", [])
        print(f"  {slug}: {title} {tags}")


def cmd_ask(prompt, model="auto"):
    """Send a prompt and get the response."""
    conv_id = None
    msg_id = str(uuid.uuid4())
    parent_id = str(uuid.uuid4())

    payload = {
        "action": "next",
        "messages": [
            {
                "id": msg_id,
                "author": {"role": "user"},
                "content": {
                    "content_type": "text",
                    "parts": [prompt]
                },
                "metadata": {}
            }
        ],
        "parent_message_id": parent_id,
        "model": model,
        "timezone_offset_sec": -21600,  # CDT
        "history_and_training_disabled": False,
        "conversation_mode": {"kind": "primary_assistant"},
        "force_paragen": False,
        "force_paragen_model_slug": "",
        "force_nulligen": False,
        "force_rate_limit": False,
    }

    # Use streaming to get the response
    resp = api_request("POST", "/conversation", payload, stream=True)

    full_text = ""
    try:
        buffer = ""
        for chunk in iter(lambda: resp.read(4096).decode("utf-8", errors="replace"), ""):
            if not chunk:
                break
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    msg = data.get("message", {})
                    if msg.get("author", {}).get("role") == "assistant":
                        parts = msg.get("content", {}).get("parts", [])
                        if parts:
                            full_text = parts[0]
                except (json.JSONDecodeError, KeyError):
                    continue
    except Exception as e:
        if not full_text:
            print(f"ERROR: Stream failed: {e}")
            sys.exit(1)
    finally:
        resp.close()

    if full_text:
        print(full_text.strip())
    else:
        print("ERROR: No response received from ChatGPT.")


def main():
    parser = argparse.ArgumentParser(description="ChatGPT Integration for GoonBot")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Check login status")
    sub.add_parser("models", help="List available models")

    setup_p = sub.add_parser("setup", help="Save session token")
    setup_p.add_argument("token", help="Session token from browser cookies")

    ask_p = sub.add_parser("ask", help="Send prompt to ChatGPT")
    ask_p.add_argument("prompt", help="The prompt to send")
    ask_p.add_argument("--model", default="auto", help="Model (auto, gpt-4o, gpt-4o-mini, o1, etc.)")
    ask_p.add_argument("--timeout", type=int, default=120, help="Max wait seconds")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args.token)
    elif args.command == "status":
        cmd_status()
    elif args.command == "models":
        cmd_models()
    elif args.command == "ask":
        cmd_ask(args.prompt, model=args.model)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
