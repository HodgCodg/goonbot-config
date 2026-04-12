#!/usr/bin/env python3
"""
UniFi Network Controller skill for GoonBot.
Talks to UniFi controller API at 10.11.0.173.

Usage:
  python3 unifi.py clients              # List connected clients
  python3 unifi.py devices              # List network devices (APs, switches, etc.)
  python3 unifi.py client NAME_OR_MAC   # Get details on a specific client
  python3 unifi.py block MAC            # Block a client by MAC
  python3 unifi.py unblock MAC          # Unblock a client
  python3 unifi.py reconnect MAC        # Force client to reconnect
  python3 unifi.py health               # Network health overview
  python3 unifi.py alerts               # Recent alerts
  python3 unifi.py dpi [MAC]            # DPI/traffic stats (all or specific client)
  python3 unifi.py setup USER PASS      # Save credentials
"""

import sys
import os
import json
import ssl
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse

CONFIG_FILE = os.path.expanduser("~/.config/goonbot/unifi.json")
CONTROLLER_URL = "https://10.11.0.173:8443"
# Try common UniFi ports
UNIFI_PORTS = [8443, 443]


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)


class UniFiAPI:
    def __init__(self):
        cfg = load_config()
        self.username = cfg.get("username", "")
        self.password = cfg.get("password", "")
        self.base_url = cfg.get("url", CONTROLLER_URL)
        self.site = cfg.get("site", "default")

        if not self.username or not self.password:
            print("ERROR: No UniFi credentials configured.")
            print("Run: python3 unifi.py setup USERNAME PASSWORD")
            sys.exit(1)

        # SSL context that ignores self-signed certs
        self.ssl_ctx = ssl.create_default_context()
        self.ssl_ctx.check_hostname = False
        self.ssl_ctx.verify_mode = ssl.CERT_NONE

        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=self.ssl_ctx)
        )
        self._logged_in = False

    def login(self):
        if self._logged_in:
            return
        # Try UniFi OS login first (newer), then legacy
        for endpoint in ["/api/auth/login", "/api/login"]:
            try:
                data = json.dumps({"username": self.username, "password": self.password}).encode()
                req = urllib.request.Request(
                    f"{self.base_url}{endpoint}",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                resp = self.opener.open(req, timeout=10)
                self._logged_in = True
                # Detect if UniFi OS (newer consoles)
                if endpoint == "/api/auth/login":
                    self._unifi_os = True
                else:
                    self._unifi_os = False
                return
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
                body = e.read().decode() if e.fp else ""
                if e.code == 401:
                    print(f"ERROR: Invalid UniFi credentials")
                    sys.exit(1)
                continue
            except urllib.error.URLError:
                continue
        print(f"ERROR: Cannot connect to UniFi controller at {self.base_url}")
        print("Try different ports: python3 unifi.py setup USER PASS [URL]")
        sys.exit(1)

    def api(self, method, path, data=None):
        self.login()
        # UniFi OS uses /proxy/network prefix
        if hasattr(self, '_unifi_os') and self._unifi_os:
            full_path = f"/proxy/network{path}"
        else:
            full_path = path

        url = f"{self.base_url}{full_path}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method=method)
        try:
            resp = self.opener.open(req, timeout=15)
            result = json.loads(resp.read().decode())
            return result.get("data", result)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200] if e.fp else ""
            print(f"ERROR: HTTP {e.code}: {body}")
            sys.exit(1)

    def get_clients(self):
        return self.api("GET", f"/api/s/{self.site}/stat/sta")

    def get_devices(self):
        return self.api("GET", f"/api/s/{self.site}/stat/device")

    def get_health(self):
        return self.api("GET", f"/api/s/{self.site}/stat/health")

    def get_alerts(self):
        return self.api("GET", f"/api/s/{self.site}/stat/alarm")

    def cmd_client(self, mac):
        return self.api("POST", f"/api/s/{self.site}/stat/user/{mac}")

    def block_client(self, mac):
        return self.api("POST", f"/api/s/{self.site}/cmd/stamgr", {"cmd": "block-sta", "mac": mac.lower()})

    def unblock_client(self, mac):
        return self.api("POST", f"/api/s/{self.site}/cmd/stamgr", {"cmd": "unblock-sta", "mac": mac.lower()})

    def reconnect_client(self, mac):
        return self.api("POST", f"/api/s/{self.site}/cmd/stamgr", {"cmd": "kick-sta", "mac": mac.lower()})

    def get_dpi(self):
        return self.api("GET", f"/api/s/{self.site}/stat/dpi")


def format_bytes(b):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(b) < 1024.0:
            return f"{b:.1f}{unit}"
        b /= 1024.0
    return f"{b:.1f}PB"


def format_uptime(seconds):
    if not seconds:
        return "N/A"
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    return " ".join(parts) or "0m"


def cmd_clients(api):
    clients = api.get_clients()
    if not clients:
        print("No connected clients.")
        return
    print(f"Connected Clients ({len(clients)}):\n")
    # Sort by hostname/name
    clients.sort(key=lambda c: (c.get("hostname") or c.get("name") or c.get("mac", "")).lower())
    for c in clients:
        name = c.get("hostname") or c.get("name") or "Unknown"
        mac = c.get("mac", "?")
        ip = c.get("ip", "no IP")
        rx = format_bytes(c.get("rx_bytes", 0))
        tx = format_bytes(c.get("tx_bytes", 0))
        up = format_uptime(c.get("uptime", 0))
        net = c.get("network", c.get("essid", "wired"))
        print(f"  {name:<25} {ip:<16} {mac}  {net}  up:{up}  rx:{rx} tx:{tx}")


def cmd_devices(api):
    devices = api.get_devices()
    if not devices:
        print("No devices found.")
        return
    print(f"Network Devices ({len(devices)}):\n")
    for d in devices:
        name = d.get("name", d.get("model", "Unknown"))
        model = d.get("model", "?")
        ip = d.get("ip", "?")
        mac = d.get("mac", "?")
        status = "ONLINE" if d.get("state") == 1 else "OFFLINE"
        uptime = format_uptime(d.get("uptime", 0))
        version = d.get("version", "?")
        clients = d.get("num_sta", 0)
        print(f"  {name:<25} {model:<12} {ip:<16} {status}  up:{uptime}  v{version}  clients:{clients}")


def cmd_client_detail(api, search):
    clients = api.get_clients()
    # Search by name or MAC
    search_lower = search.lower()
    matches = [c for c in clients if
               search_lower in (c.get("hostname") or "").lower() or
               search_lower in (c.get("name") or "").lower() or
               search_lower == c.get("mac", "").lower() or
               search_lower == c.get("ip", "")]
    if not matches:
        print(f"No client found matching '{search}'")
        return
    for c in matches:
        name = c.get("hostname") or c.get("name") or "Unknown"
        print(f"Name: {name}")
        print(f"MAC: {c.get('mac', '?')}")
        print(f"IP: {c.get('ip', 'N/A')}")
        print(f"Network: {c.get('network', c.get('essid', 'wired'))}")
        print(f"Uptime: {format_uptime(c.get('uptime', 0))}")
        print(f"Signal: {c.get('signal', 'N/A')} dBm")
        print(f"RX: {format_bytes(c.get('rx_bytes', 0))} TX: {format_bytes(c.get('tx_bytes', 0))}")
        print(f"Blocked: {c.get('blocked', False)}")
        if c.get("oui"):
            print(f"Vendor: {c['oui']}")
        print()


def cmd_health(api):
    health = api.get_health()
    if not health:
        print("Could not get health info.")
        return
    print("Network Health:\n")
    for subsys in health:
        name = subsys.get("subsystem", "?")
        status = subsys.get("status", "?")
        num_adopted = subsys.get("num_adopted", "?")
        print(f"  {name}: {status} (adopted: {num_adopted})")
        if "wan_ip" in subsys:
            print(f"    WAN IP: {subsys['wan_ip']}")
        if "rx_bytes-r" in subsys:
            print(f"    RX rate: {format_bytes(subsys['rx_bytes-r'])}/s")
        if "tx_bytes-r" in subsys:
            print(f"    TX rate: {format_bytes(subsys['tx_bytes-r'])}/s")
        if "num_user" in subsys:
            print(f"    Users: {subsys['num_user']}")


def cmd_alerts(api):
    alerts = api.get_alerts()
    if not alerts:
        print("No recent alerts.")
        return
    print(f"Recent Alerts ({len(alerts)}):\n")
    for a in alerts[:15]:
        ts = a.get("datetime", a.get("time", "?"))
        msg = a.get("msg", a.get("key", "?"))
        print(f"  [{ts[:19]}] {msg}")


def cmd_setup(username, password, url=None):
    cfg = {
        "username": username,
        "password": password,
        "url": url or CONTROLLER_URL,
        "site": "default"
    }
    save_config(cfg)
    # Try to connect
    api = UniFiAPI()
    api.login()
    print(f"OK: Connected to UniFi controller at {cfg['url']}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "setup":
        if len(sys.argv) < 4:
            print("Usage: unifi.py setup USERNAME PASSWORD [CONTROLLER_URL]")
            sys.exit(1)
        cmd_setup(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
        return

    api = UniFiAPI()

    if cmd == "clients":
        cmd_clients(api)
    elif cmd == "devices":
        cmd_devices(api)
    elif cmd == "client" and len(sys.argv) >= 3:
        cmd_client_detail(api, sys.argv[2])
    elif cmd == "block" and len(sys.argv) >= 3:
        api.block_client(sys.argv[2])
        print(f"Blocked: {sys.argv[2]}")
    elif cmd == "unblock" and len(sys.argv) >= 3:
        api.unblock_client(sys.argv[2])
        print(f"Unblocked: {sys.argv[2]}")
    elif cmd == "reconnect" and len(sys.argv) >= 3:
        api.reconnect_client(sys.argv[2])
        print(f"Reconnecting: {sys.argv[2]}")
    elif cmd == "health":
        cmd_health(api)
    elif cmd == "alerts":
        cmd_alerts(api)
    elif cmd == "dpi":
        result = api.get_dpi()
        print(json.dumps(result, indent=2)[:3000] if result else "No DPI data")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
