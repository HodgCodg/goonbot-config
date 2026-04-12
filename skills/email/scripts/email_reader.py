#!/usr/bin/env python3
"""
Email reader for GoonBot via IMAP (O365/Exchange compatible).
Reads emails to extract 2FA codes and other automated tasks.

Setup:
  python3 email_reader.py setup EMAIL PASSWORD [--server SERVER] [--port PORT]

Usage:
  python3 email_reader.py inbox [N]                    # Show last N emails (default 5)
  python3 email_reader.py read MESSAGE_ID              # Read specific email
  python3 email_reader.py search "QUERY" [N]           # Search emails
  python3 email_reader.py 2fa [MINUTES]                # Find most recent 2FA code (default: last 5 min)
  python3 email_reader.py wait2fa [TIMEOUT] [INTERVAL] # Wait for a 2FA email (default: 120s timeout, 5s poll)
  python3 email_reader.py status                       # Check connection
"""

import sys
import os
import json
import imaplib
import email
import email.header
import email.utils
import re
import time
import html
from datetime import datetime, timedelta

CONFIG_DIR = os.path.expanduser("~/.config/goonbot")
CONFIG_FILE = os.path.join(CONFIG_DIR, "email.json")

# Common 2FA patterns
TFA_PATTERNS = [
    r'\b(\d{6})\b',  # 6-digit codes
    r'\b(\d{4})\b',  # 4-digit codes
    r'(?:code|pin|otp|token|verification)[:\s]+(\d{4,8})',
    r'(\d{4,8})[:\s]+(?:is your|verification|code)',
]

TFA_SUBJECT_KEYWORDS = [
    'verification', 'verify', 'code', '2fa', 'two-factor',
    'sign in', 'sign-in', 'login', 'authenticate', 'security',
    'one-time', 'otp', 'confirm', 'access code',
]


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def connect_imap(cfg):
    """Connect to IMAP server and login."""
    server = cfg.get("server", "outlook.office365.com")
    port = cfg.get("port", 993)

    imap = imaplib.IMAP4_SSL(server, port)
    imap.login(cfg["email"], cfg["password"])
    return imap


def decode_header_value(raw):
    """Decode email header (handles encoded words)."""
    if not raw:
        return ""
    parts = email.header.decode_header(raw)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            result.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(data)
    return " ".join(result)


def get_body(msg):
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
            elif ct == "text/html" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                    # Strip HTML tags
                    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = html.unescape(text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def extract_2fa_code(subject, body):
    """Try to extract a 2FA code from email subject and body."""
    text = f"{subject} {body}"
    for pattern in TFA_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def is_2fa_email(subject):
    """Check if email subject suggests it's a 2FA email."""
    subj_lower = subject.lower()
    return any(kw in subj_lower for kw in TFA_SUBJECT_KEYWORDS)


def format_email_summary(msg, msg_id):
    """Format email for display."""
    subject = decode_header_value(msg.get("Subject", "(no subject)"))
    sender = decode_header_value(msg.get("From", "unknown"))
    date = msg.get("Date", "unknown")
    return f"[{msg_id}] {date}\n  From: {sender}\n  Subject: {subject}"


def cmd_setup(args):
    """Store email credentials."""
    if len(args) < 2:
        print("Usage: email_reader.py setup EMAIL PASSWORD [--server SERVER] [--port PORT]")
        sys.exit(1)

    cfg = load_config()
    cfg["email"] = args[0]
    cfg["password"] = args[1]
    cfg["server"] = "outlook.office365.com"
    cfg["port"] = 993

    # Parse optional args
    i = 2
    while i < len(args):
        if args[i] == "--server" and i + 1 < len(args):
            cfg["server"] = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            cfg["port"] = int(args[i + 1])
            i += 2
        else:
            i += 1

    # Test connection
    try:
        imap = connect_imap(cfg)
        imap.select("INBOX", readonly=True)
        status, data = imap.search(None, "ALL")
        count = len(data[0].split()) if data[0] else 0
        imap.logout()
        save_config(cfg)
        print(f"OK: Connected to {cfg['server']} as {cfg['email']}")
        print(f"Inbox: {count} messages")
    except imaplib.IMAP4.error as e:
        print(f"ERROR: IMAP login failed: {e}")
        print("If using O365 with 2FA, you may need an app password or OAuth.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        sys.exit(1)


def cmd_inbox(n=5):
    """Show last N emails."""
    cfg = load_config()
    if not cfg.get("email"):
        print("ERROR: Not configured. Run: email_reader.py setup EMAIL PASSWORD")
        sys.exit(1)

    imap = connect_imap(cfg)
    imap.select("INBOX", readonly=True)
    status, data = imap.search(None, "ALL")
    msg_ids = data[0].split()

    if not msg_ids:
        print("Inbox is empty.")
        imap.logout()
        return

    # Get last N
    recent = msg_ids[-n:]
    recent.reverse()

    for msg_id in recent:
        status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
        if status == "OK":
            msg = email.message_from_bytes(msg_data[0][1])
            print(format_email_summary(msg, msg_id.decode()))
            print()

    imap.logout()


def cmd_read(msg_id):
    """Read specific email by ID."""
    cfg = load_config()
    if not cfg.get("email"):
        print("ERROR: Not configured.")
        sys.exit(1)

    imap = connect_imap(cfg)
    imap.select("INBOX", readonly=True)
    status, msg_data = imap.fetch(str(msg_id), "(RFC822)")

    if status != "OK":
        print(f"ERROR: Could not fetch message {msg_id}")
        imap.logout()
        sys.exit(1)

    msg = email.message_from_bytes(msg_data[0][1])
    subject = decode_header_value(msg.get("Subject", "(no subject)"))
    sender = decode_header_value(msg.get("From", "unknown"))
    date = msg.get("Date", "unknown")
    body = get_body(msg)

    print(f"From: {sender}")
    print(f"Date: {date}")
    print(f"Subject: {subject}")
    print(f"---")
    print(body[:2000])

    imap.logout()


def cmd_search(query, n=5):
    """Search emails."""
    cfg = load_config()
    if not cfg.get("email"):
        print("ERROR: Not configured.")
        sys.exit(1)

    imap = connect_imap(cfg)
    imap.select("INBOX", readonly=True)

    # IMAP search
    search_criteria = f'(OR SUBJECT "{query}" FROM "{query}")'
    status, data = imap.search(None, search_criteria)
    msg_ids = data[0].split()

    if not msg_ids:
        print(f"No emails matching '{query}'")
        imap.logout()
        return

    recent = msg_ids[-n:]
    recent.reverse()

    for msg_id in recent:
        status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
        if status == "OK":
            msg = email.message_from_bytes(msg_data[0][1])
            print(format_email_summary(msg, msg_id.decode()))
            print()

    imap.logout()


def cmd_2fa(minutes=5):
    """Find most recent 2FA code from inbox."""
    cfg = load_config()
    if not cfg.get("email"):
        print("ERROR: Not configured.")
        sys.exit(1)

    imap = connect_imap(cfg)
    imap.select("INBOX", readonly=True)

    # Search recent emails
    since = (datetime.utcnow() - timedelta(minutes=minutes)).strftime("%d-%b-%Y")
    status, data = imap.search(None, f'(SINCE {since})')
    msg_ids = data[0].split()

    if not msg_ids:
        print("NO_CODE: No recent emails found")
        imap.logout()
        return

    # Check from newest to oldest
    msg_ids.reverse()
    for msg_id in msg_ids:
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        subject = decode_header_value(msg.get("Subject", ""))

        if is_2fa_email(subject):
            body = get_body(msg)
            code = extract_2fa_code(subject, body)
            if code:
                sender = decode_header_value(msg.get("From", "unknown"))
                print(f"CODE: {code}")
                print(f"from: {sender}")
                print(f"subject: {subject}")
                imap.logout()
                return

    print("NO_CODE: No 2FA emails found in last {minutes} minutes")
    imap.logout()


def cmd_wait2fa(timeout=120, interval=5):
    """Poll inbox for a new 2FA code."""
    cfg = load_config()
    if not cfg.get("email"):
        print("ERROR: Not configured.")
        sys.exit(1)

    start = time.time()
    # Mark current time as baseline
    baseline = datetime.utcnow()

    print(f"Waiting for 2FA email (timeout: {timeout}s, poll: {interval}s)...")

    while time.time() - start < timeout:
        try:
            imap = connect_imap(cfg)
            imap.select("INBOX", readonly=True)

            since = baseline.strftime("%d-%b-%Y")
            status, data = imap.search(None, f'(SINCE {since})')
            msg_ids = data[0].split()

            if msg_ids:
                # Check newest messages
                for msg_id in reversed(msg_ids):
                    status, msg_data = imap.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])
                    # Check if this email arrived after our baseline
                    date_str = msg.get("Date", "")
                    msg_date = email.utils.parsedate_to_datetime(date_str) if date_str else None

                    subject = decode_header_value(msg.get("Subject", ""))
                    if is_2fa_email(subject):
                        body = get_body(msg)
                        code = extract_2fa_code(subject, body)
                        if code:
                            sender = decode_header_value(msg.get("From", "unknown"))
                            elapsed = int(time.time() - start)
                            print(f"CODE: {code}")
                            print(f"from: {sender}")
                            print(f"subject: {subject}")
                            print(f"elapsed: {elapsed}s")
                            imap.logout()
                            return

            imap.logout()
        except Exception as e:
            print(f"Poll error: {e}", file=sys.stderr)

        time.sleep(interval)

    print(f"TIMEOUT: No 2FA email received in {timeout}s")
    sys.exit(1)


def cmd_status():
    """Check connection status."""
    cfg = load_config()
    if not cfg.get("email"):
        print("NOT_SETUP: Run email_reader.py setup EMAIL PASSWORD")
        sys.exit(0)

    try:
        imap = connect_imap(cfg)
        imap.select("INBOX", readonly=True)
        status, data = imap.search(None, "ALL")
        count = len(data[0].split()) if data[0] else 0
        imap.logout()
        print(f"OK: {cfg['email']} via {cfg.get('server', 'unknown')}")
        print(f"Inbox: {count} messages")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "setup":
        cmd_setup(sys.argv[2:])
    elif cmd == "inbox":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        cmd_inbox(n)
    elif cmd == "read" and len(sys.argv) > 2:
        cmd_read(sys.argv[2])
    elif cmd == "search" and len(sys.argv) > 2:
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        cmd_search(sys.argv[2], n)
    elif cmd == "2fa":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        cmd_2fa(minutes)
    elif cmd == "wait2fa":
        timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        cmd_wait2fa(timeout, interval)
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__.strip())
        sys.exit(1)


if __name__ == "__main__":
    main()
