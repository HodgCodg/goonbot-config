#!/usr/bin/env python3
"""
TOTP code generator for GoonBot.
Generates 2FA codes from stored secrets so GoonBot can authenticate autonomously.

Usage:
  python3 totp.py setup NAME SECRET       # Store a TOTP secret
  python3 totp.py code NAME               # Generate current code
  python3 totp.py list                    # List stored accounts
  python3 totp.py remove NAME             # Remove an account
"""

import sys
import os
import json
import time
import hmac
import hashlib
import struct
import base64

CONFIG_DIR = os.path.expanduser("~/.config/goonbot")
CONFIG_FILE = os.path.join(CONFIG_DIR, "totp.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"accounts": {}}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def generate_totp(secret, period=30, digits=6):
    """Generate TOTP code from secret — pure Python, no dependencies."""
    # Normalize secret
    secret = secret.upper().replace(" ", "").replace("-", "")
    # Pad base32 if needed
    padding = 8 - (len(secret) % 8)
    if padding != 8:
        secret += "=" * padding
    key = base64.b32decode(secret)

    # Time counter
    counter = int(time.time()) // period
    counter_bytes = struct.pack(">Q", counter)

    # HMAC-SHA1
    h = hmac.new(key, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = h[-1] & 0x0F
    code_int = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    code = code_int % (10 ** digits)

    remaining = period - (int(time.time()) % period)
    return f"{code:0{digits}d}", remaining


def cmd_setup(name, secret):
    """Store a TOTP secret."""
    # Validate the secret works
    try:
        code, _ = generate_totp(secret)
    except Exception as e:
        print(f"ERROR: Invalid TOTP secret: {e}")
        sys.exit(1)

    cfg = load_config()
    cfg["accounts"][name.lower()] = {
        "secret": secret.upper().replace(" ", "").replace("-", ""),
        "added": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_config(cfg)
    print(f"OK: Stored TOTP for '{name}' (test code: {code})")


def cmd_code(name):
    """Generate current TOTP code."""
    cfg = load_config()
    account = cfg.get("accounts", {}).get(name.lower())
    if not account:
        print(f"ERROR: No TOTP account '{name}'. Run: totp.py list")
        sys.exit(1)

    code, remaining = generate_totp(account["secret"])
    print(f"{code}")
    print(f"expires_in={remaining}s")


def cmd_list():
    """List stored accounts."""
    cfg = load_config()
    accounts = cfg.get("accounts", {})
    if not accounts:
        print("No TOTP accounts configured.")
        return
    for name, info in accounts.items():
        print(f"  {name} (added {info.get('added', 'unknown')})")


def cmd_remove(name):
    """Remove an account."""
    cfg = load_config()
    if name.lower() in cfg.get("accounts", {}):
        del cfg["accounts"][name.lower()]
        save_config(cfg)
        print(f"OK: Removed '{name}'")
    else:
        print(f"ERROR: No account '{name}'")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "setup" and len(sys.argv) == 4:
        cmd_setup(sys.argv[2], sys.argv[3])
    elif cmd == "code" and len(sys.argv) == 3:
        cmd_code(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    elif cmd == "remove" and len(sys.argv) == 3:
        cmd_remove(sys.argv[2])
    else:
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
