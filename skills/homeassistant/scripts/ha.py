#!/usr/bin/env python3
"""
Home Assistant control skill for GoonBot.
Talks to HA REST API at 10.11.0.173:8123.

Usage:
  python3 ha.py areas                         # List all areas/rooms with entity counts
  python3 ha.py area AREA                     # Show entities in a room (e.g. 'living_room')
  python3 ha.py room_on AREA                  # Turn on all lights/switches in a room
  python3 ha.py room_off AREA                 # Turn off all lights/switches in a room
  python3 ha.py find NAME                     # Find entity by friendly name or partial match
  python3 ha.py states [DOMAIN]              # List all entity states (or filter by domain)
  python3 ha.py entity ENTITY_ID             # Get detailed state of one entity
  python3 ha.py toggle ENTITY_ID             # Toggle entity
  python3 ha.py turn_on ENTITY_ID            # Turn on entity
  python3 ha.py turn_off ENTITY_ID           # Turn off entity
  python3 ha.py set ENTITY_ID KEY=VAL        # Set attributes (e.g. brightness=128)
  python3 ha.py scene SCENE_ID               # Activate a scene
  python3 ha.py automation list              # List all automations
  python3 ha.py automation trigger ID        # Trigger an automation
  python3 ha.py climate ENTITY TEMP          # Set thermostat temperature
  python3 ha.py call DOMAIN SERVICE JSON     # Call any service with JSON data
  python3 ha.py history ENTITY [HOURS]       # Get entity history (default 24h)
  python3 ha.py setup TOKEN                  # Save API token to config file
  python3 ha.py config                       # Show HA config info

TIPS:
  - Use 'areas' first to see room names, then 'area ROOM' to see entity IDs
  - Use 'find NAME' to locate an entity by its friendly name
  - Room names use underscores: living_room, master_bedroom, game_room, etc.
  - Prefer light.* entities for dimmable bulbs; switch.* for wall outlets/plugs
"""

import json
import os
import sys
import re
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

HA_URL = "http://10.11.0.173:8123"
CONFIG_FILE = os.path.expanduser("~/.config/goonbot/ha.json")

# Domains that are controllable (shown in area views)
CONTROLLABLE_DOMAINS = {"light", "switch", "climate", "cover", "fan", "media_player", "lock", "input_boolean"}

# Areas to hide from the areas list (utility groups, remote sites, empty stubs)
EXCLUDE_AREAS = {
    "beloit", "remote_sites", "power_usage",
    "thermostats", "thermostat", "christmas_lights",
    "attic", "back_patio", "pantry", "bedroom",  # empty stub areas
}

# Internal/diagnostic entity patterns to suppress
_NOISE_PATTERNS = re.compile(
    r"(0x[0-9a-f]+|_node_identify|_button_\d+_indication|_last_seen|_rssi|_lqi|_power_on_behavior)",
    re.I,
)

# Remote-site entity prefixes to filter out (Austin, Beloit off-site devices)
_REMOTE_PATTERNS = re.compile(r"(austin|beloit)", re.I)


# ---------------------------------------------------------------------------
# Config / auth
# ---------------------------------------------------------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_token():
    cfg = load_config()
    token = cfg.get("token") or os.environ.get("HA_TOKEN")
    if not token:
        print("ERROR: No HA API token configured.")
        print("Run: python3 ha.py setup YOUR_LONG_LIVED_ACCESS_TOKEN")
        sys.exit(1)
    return token


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_request(method, path, data=None, token=None):
    if token is None:
        token = get_token()
    url = f"{HA_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw  # template endpoint returns plain strings
    except urllib.error.HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"ERROR: HTTP {e.code} from HA API: {body_text[:300]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach HA at {HA_URL}: {e.reason}")
        sys.exit(1)

def template(tmpl):
    """Render a Jinja2 template via HA's /api/template endpoint."""
    result = api_request("POST", "/api/template", {"template": tmpl})
    if isinstance(result, str):
        try:
            return json.loads(result)
        except Exception:
            return result
    return result

def get_states():
    """Return all states as a dict keyed by entity_id."""
    return {s["entity_id"]: s for s in api_request("GET", "/api/states")}


# ---------------------------------------------------------------------------
# Area helpers
# ---------------------------------------------------------------------------

def get_all_areas_bulk():
    """
    Single template call that returns:
      { area_id: { "name": "Display Name", "entities": [...] }, ... }
    Much faster than one call per area.
    """
    tmpl = (
        "{%- set ns = namespace(r={}) -%}"
        "{%- for a in areas() -%}"
        "{%- set ns.r = dict(ns.r, **{a: {'name': area_name(a), 'entities': area_entities(a) | list}}) -%}"
        "{%- endfor -%}"
        "{{ ns.r | tojson }}"
    )
    result = template(tmpl)
    return result if isinstance(result, dict) else {}

def get_areas():
    """Return list of area_id strings."""
    return template("{{ areas() | tojson }}")

def get_area_entities(area_id):
    """Return list of entity_id strings in the given area."""
    result = template(f'{{{{ area_entities("{area_id}") | tojson }}}}')
    return result if isinstance(result, list) else []

def is_noisy(entity_id):
    """Return True for internal/diagnostic Z-Wave/Zigbee entities."""
    return bool(_NOISE_PATTERNS.search(entity_id))

def is_remote(entity_id):
    """Return True for Austin/Beloit off-site entities."""
    return bool(_REMOTE_PATTERNS.search(entity_id))

def dedup_entities(entity_ids):
    """
    Filter and deduplicate entity list:
    - Remove noisy diagnostic entities
    - Remove remote (Austin/Beloit) entities
    - When switch.foo and light.foo both exist, keep only light.foo
    """
    clean = [e for e in entity_ids if not is_noisy(e) and not is_remote(e)]
    light_names = {e.split(".", 1)[1] for e in clean if e.startswith("light.")}
    deduped = []
    for e in clean:
        domain, name = e.split(".", 1)
        if domain == "switch" and name in light_names:
            continue
        deduped.append(e)
    return deduped


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_setup(token):
    save_config({"token": token, "url": HA_URL})
    try:
        result = api_request("GET", "/api/", token=token)
        print(f"OK: Connected to Home Assistant {result.get('version', '')}")
    except SystemExit:
        print("WARNING: Token saved but connection test failed.")

def cmd_config():
    result = api_request("GET", "/api/config")
    print(f"HA Version : {result.get('version')}")
    print(f"Location   : {result.get('location_name')}")
    print(f"Timezone   : {result.get('time_zone')}")
    print(f"Components : {len(result.get('components', []))} loaded")

def cmd_states(domain=None):
    states = api_request("GET", "/api/states")
    if domain:
        states = [s for s in states if s["entity_id"].startswith(domain + ".")]
    # Filter remote entities
    states = [s for s in states if not is_remote(s["entity_id"])]
    by_domain = {}
    for s in states:
        d = s["entity_id"].split(".")[0]
        by_domain.setdefault(d, []).append(s)
    for d, items in sorted(by_domain.items()):
        print(f"\n--- {d} ({len(items)}) ---")
        for s in items:
            name = s["attributes"].get("friendly_name", s["entity_id"])
            print(f"  {s['entity_id']}: {s['state']} ({name})")

def cmd_entity(entity_id):
    s = api_request("GET", f"/api/states/{entity_id}")
    print(f"Entity  : {s['entity_id']}")
    print(f"State   : {s['state']}")
    print(f"Updated : {s.get('last_changed', '?')}")
    attrs = s.get("attributes", {})
    for k, v in attrs.items():
        print(f"  {k}: {v}")

def cmd_areas():
    """List all local areas with controllable entity counts (single bulk API call)."""
    area_data = get_all_areas_bulk()
    states = get_states()

    # Filter to local, non-empty areas only
    rows = []
    for area_id, info in area_data.items():
        if area_id in EXCLUDE_AREAS:
            continue
        entities = info.get("entities", [])
        controllable = dedup_entities([
            e for e in entities
            if e.split(".")[0] in CONTROLLABLE_DOMAINS
        ])
        on_count = sum(
            1 for e in controllable
            if states.get(e, {}).get("state") in ("on", "heat", "cool", "auto", "open")
        )
        total = len(controllable)
        if total == 0:
            continue  # skip empty areas
        display_name = info.get("name", area_id)
        rows.append((area_id, display_name, on_count, total))

    rows.sort(key=lambda r: r[0])
    print(f"Areas ({len(rows)} with devices):\n")
    for area_id, display_name, on_count, total in rows:
        status = f"{on_count}/{total} on"
        print(f"  {area_id:<25} {display_name:<22} [{status}]")

def cmd_area(area_id):
    """Show controllable entities in an area with their current states."""
    area_id = area_id.lower().replace(" ", "_")
    all_areas = get_areas()
    if area_id not in all_areas:
        matches = [a for a in all_areas if area_id in a]
        if len(matches) == 1:
            area_id = matches[0]
        elif len(matches) > 1:
            print(f"Ambiguous area '{area_id}'. Matches: {matches}")
            sys.exit(1)
        else:
            print(f"Area '{area_id}' not found. Run 'python3 ha.py areas' for valid names.")
            sys.exit(1)

    entities = get_area_entities(area_id)
    states = get_states()
    controllable = dedup_entities([
        e for e in entities if e.split(".")[0] in CONTROLLABLESDOMAINS
    ])

    # Get proper display name from HA
    display_name = template(f'{{{{ area_name("{area_id}") }}}}') or area_id.replace("_", " ").title()
    print(f"\n=== {display_name} ===\n")
    if not controllable:
        print("  (no controllable devices)")
        return

    by_domain = {}
    for e in controllable:
        d = e.split(".")[0]
        by_domain.setdefault(d, []).append(e)

    for domain in sorted(by_domain):
        print(f"  [{domain}]")
        for eid in by_domain[domain]:
            s = states.get(eid, {})
            state = s.get("state", "?")
            attrs = s.get("attributes", {})
            name = attrs.get("friendly_name", eid)
            extra = ""
            if domain == "light" and state == "on":
                bright = attrs.get("brightness")
                if bright is not None:
                    extra = f" @ {round(bright / 2.55)}%"
            elif domain == "climate":
                temp = attrs.get("current_temperature")
                target = attrs.get("temperature")
                if temp is not None:
                    extra = f" (cur:{temp}° set:{target}°)"
            print(f"    {eid}: {state}{extra}  # {name}")

def cmd_room_on(area_id):
    """Turn on all lights and switches in a room."""
    _room_control(area_id, "turn_on")

def cmd_room_off(area_id):
    """Turn off all lights and switches in a room."""
    _room_control(area_id, "turn_off")

def _room_control(area_id, action):
    area_id = area_id.lower().replace(" ", "_")
    all_areas = get_areas()
    if area_id not in all_areas:
        matches = [a for a in all_areas if area_id in a]
        if len(matches) == 1:
            area_id = matches[0]
        else:
            print(f"Area '{area_id}' not found. Run 'python3 ha.py areas' to list them.")
            sys.exit(1)

    entities = get_area_entities(area_id)
    controllable = dedup_entities([
        e for e in entities
        if e.split(".")[0] in {"light", "switch"}
    ])

    if not controllable:
        print(f"No lights or switches found in '{area_id}'.")
        return

    for eid in controllable:
        domain = eid.split(".")[0]
        api_request("POST", f"/api/services/{domain}/{action}", {"entity_id": eid})
        name = eid.split(".", 1)[1].replace("_", " ").title()
        print(f"  {action}: {eid}  # {name}")

    display = template(f'{{{{ area_name("{area_id}") }}}}') or area_id.replace("_", " ").title()
    print(f"\nOK: {action.replace('_', ' ').title()} {len(controllable)} device(s) in {display}")

def cmd_find(query):
    """Find entities by friendly name or entity_id substring."""
    query = query.lower()
    states = api_request("GET", "/api/states")
    matches = []
    for s in states:
        eid = s["entity_id"]
        if is_remote(eid):
            continue
        name = s.get("attributes", {}).get("friendly_name", "").lower()
        if query in eid.lower() or query in name:
            matches.append(s)

    if not matches:
        print(f"No entities found matching '{query}'.")
        return
    print(f"Found {len(matches)} match(es) for '{query}':\n")
    for s in matches:
        name = s["attributes"].get("friendly_name", s["entity_id"])
        print(f"  {s['entity_id']}: {s['state']}  # {name}")

def cmd_service(domain, service, entity_id=None, extra_data=None):
    data = {}
    if entity_id:
        data["entity_id"] = entity_id
    if extra_data:
        data.update(extra_data)
    result = api_request("POST", f"/api/services/{domain}/{service}", data)
    if isinstance(result, list) and result:
        for s in result[:5]:
            name = s.get("attributes", {}).get("friendly_name", s.get("entity_id", ""))
            print(f"  {s.get('entity_id', '?')}: {s.get('state', '?')} ({name})")
    else:
        print(f"OK: {domain}/{service} called successfully")

def cmd_toggle(entity_id):
    domain = entity_id.split(".")[0]
    cmd_service(domain, "toggle", entity_id)

def cmd_turn_on(entity_id):
    domain = entity_id.split(".")[0]
    cmd_service(domain, "turn_on", entity_id)

def cmd_turn_off(entity_id):
    domain = entity_id.split(".")[0]
    cmd_service(domain, "turn_off", entity_id)

def cmd_set(entity_id, attrs):
    domain = entity_id.split(".")[0]
    extra = {}
    for attr in attrs:
        k, _, v = attr.partition("=")
        try:
            v = int(v)
        except ValueError:
            try:
                v = float(v)
            except ValueError:
                pass
        extra[k] = v
    cmd_service(domain, "turn_on", entity_id, extra)

def cmd_scene(scene_id):
    if not scene_id.startswith("scene."):
        scene_id = f"scene.{scene_id}"
    cmd_service("scene", "turn_on", scene_id)

def cmd_automation(sub, automation_id=None):
    if sub == "list":
        states = api_request("GET", "/api/states")
        autos = [s for s in states if s["entity_id"].startswith("automation.")]
        for a in autos:
            name = a["attributes"].get("friendly_name", a["entity_id"])
            print(f"  {a['entity_id']}: {a['state']}  # {name}")
    elif sub == "trigger" and automation_id:
        cmd_service("automation", "trigger", automation_id)
    else:
        print("Usage: ha.py automation list | ha.py automation trigger ENTITY_ID")

def cmd_climate(entity_id, temp):
    if not entity_id.startswith("climate."):
        entity_id = f"climate.{entity_id}"
    cmd_service("climate", "set_temperature", entity_id, {"temperature": float(temp)})

def cmd_call(domain, service, json_str):
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(1)
    cmd_service(domain, service, extra_data=data)

def cmd_history(entity_id, hours=24):
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=int(hours))
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    result = api_request("GET", f"/api/history/period/{start_str}?filter_entity_id={entity_id}&minimal_response=true")
    if not result or not result[0]:
        print(f"No history found for {entity_id}")
        return
    entries = result[0]
    print(f"History for {entity_id} (last {hours}h, {len(entries)} entries):\n")
    for e in entries[-30:]:
        ts = e.get("last_changed", "?")[:19].replace("T", " ")
        print(f"  {ts}  {e.get('state', '?')}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "setup" and len(sys.argv) >= 3:
        cmd_setup(sys.argv[2])
    elif cmd == "config":
        cmd_config()
    elif cmd == "areas":
        cmd_areas()
    elif cmd == "area" and len(sys.argv) >= 3:
        cmd_area(sys.argv[2])
    elif cmd == "room_on" and len(sys.argv) >= 3:
        cmd_room_on(sys.argv[2])
    elif cmd == "room_off" and len(sys.argv) >= 3:
        cmd_room_off(sys.argv[2])
    elif cmd == "find" and len(sys.argv) >= 3:
        cmd_find(sys.argv[2])
    elif cmd == "states":
        cmd_states(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "entity" and len(sys.argv) >= 3:
        cmd_entity(sys.argv[2])
    elif cmd == "toggle" and len(sys.argv) >= 3:
        cmd_toggle(sys.argv[2])
    elif cmd == "turn_on" and len(sys.argv) >= 3:
        cmd_turn_on(sys.argv[2])
    elif cmd == "turn_off" and len(sys.argv) >= 3:
        cmd_turn_off(sys.argv[2])
    elif cmd == "set" and len(sys.argv) >= 4:
        cmd_set(sys.argv[2], sys.argv[3:])
    elif cmd == "scene" and len(sys.argv) >= 3:
        cmd_scene(sys.argv[2])
    elif cmd == "automation" and len(sys.argv) >= 3:
        cmd_automation(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "climate" and len(sys.argv) >= 4:
        cmd_climate(sys.argv[2], sys.argv[3])
    elif cmd == "call" and len(sys.argv) >= 5:
        cmd_call(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "history" and len(sys.argv) >= 3:
        cmd_history(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 24)
    else:
        print(f"Unknown command or missing args: {sys.argv[1:]}")
        print("Run with no args for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
