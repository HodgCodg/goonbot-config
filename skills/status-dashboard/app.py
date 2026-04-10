#!/usr/bin/env python3
"""BotVM Status Dashboard - Flask web UI for monitoring system status."""

import subprocess
import json
import requests
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# Configuration
CONFIG = {
    "homeassistant": {
        "url": "http://10.11.0.173:8123",
        "token": ""  # Set this in .env or pass as env var
    },
    "pfsense": {
        "ip": "10.11.0.1",  # Adjust to your PFsense IP
        "username": "admin",
        "password": ""  # Set via env var
    }
}

def get_botvm_status():
    """Get BotVM system status."""
    try:
        # Uptime
        result = subprocess.run(['uptime', '-p'], capture_output=True, text=True)
        uptime = result.stdout.strip()
        
        # Load average
        with open('/proc/loadavg', 'r') as f:
            loadavg = f.read().split()[:3]
        
        # Memory
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        mem_lines = result.stdout.strip().split('\n')
        memory = mem_lines[1].split()[1:4]  # total, used, available
        
        # Disk
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        disk_lines = result.stdout.strip().split('\n')
        disk_parts = disk_lines[1].split()
        disk_used = disk_parts[2]
        disk_avail = disk_parts[3]
        
        # CPU temp (if available)
        try:
            result = subprocess.run(['sensors', '-j'], capture_output=True, text=True)
            sensors_data = json.loads(result.stdout)
            cpu_temp = sensors_data.get('coretemp-isa-0000', {}).get('Package id 0', {}).get('label', 'N/A')
        except:
            cpu_temp = "N/A"
        
        return {
            "uptime": uptime,
            "loadavg": loadavg,
            "memory_total": memory[0],
            "memory_used": memory[1],
            "disk_used": disk_used,
            "disk_avail": disk_avail,
            "cpu_temp": cpu_temp
        }
    except Exception as e:
        return {"error": str(e)}

def get_homeassistant_status():
    """Get Home Assistant status."""
    try:
        response = requests.get(
            f"{CONFIG['homeassistant']['url']}/api/states",
            headers={"Authorization": f"Bearer {CONFIG['homeassistant']['token']}"},
            timeout=5
        )
        if response.status_code == 200:
            states = response.json()
            return {
                "status": "online",
                "entities": len(states),
                "lights_on": sum(1 for s in states if s['state'] == 'on' and s['entity_id'].startswith('light.'))
            }
        else:
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        return {"status": "offline", "error": str(e)}

def get_pfsense_status():
    """Get PFsense router status."""
    try:
        # Simple ping check
        result = subprocess.run(['ping', '-c', '1', CONFIG['pfsense']['ip']], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "online", "latency": result.stdout}
        else:
            return {"status": "offline"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BotVM Status Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .card { transition: transform 0.2s; }
        .card:hover { transform: translateY(-2px); }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .status-online { background-color: #4ade80; }
        .status-offline { background-color: #ef4444; }
        .status-error { background-color: #fbbf24; }
    </style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-2">🦞 BotVM Status Dashboard</h1>
            <p class="text-gray-400">Last updated: {{ timestamp }}</p>
        </header>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- BotVM Status -->
            <div class="card bg-gray-800 rounded-lg p-6 shadow-lg">
                <h2 class="text-xl font-bold mb-4 flex items-center">
                    <span class="status-dot status-online mr-2"></span>
                    🖥️ BotVM
                </h2>
                <div class="space-y-2 text-sm">
                    <p><span class="text-gray-400">Uptime:</span> {{ botvm.uptime }}</p>
                    <p><span class="text-gray-400">Load Avg:</span> {{ "/ ".join(botvm.loadavg) }}</p>
                    <p><span class="text-gray-400">Memory:</span> {{ botvm.memory_used }} / {{ botvm.memory_total }}</p>
                    <p><span class="text-gray-400">Disk:</span> {{ botvm.disk_used }} used, {{ botvm.disk_avail }} free</p>
                </div>
            </div>
            
            <!-- Home Assistant Status -->
            <div class="card bg-gray-800 rounded-lg p-6 shadow-lg">
                <h2 class="text-xl font-bold mb-4 flex items-center">
                    <span class="status-dot status-{{ "online" if ha.status == "online" else "offline" }} mr-2"></span>
                    🏠 Home Assistant
                </h2>
                {% if ha.status == "online" %}
                <div class="space-y-2 text-sm">
                    <p><span class="text-gray-400">Entities:</span> {{ ha.entities }}</p>
                    <p><span class="text-gray-400">Lights On:</span> {{ ha.lights_on }}</p>
                </div>
                {% else %}
                <p class="text-sm text-red-400">Connection failed: {{ ha.error or "Offline" }}</p>
                {% endif %}
            </div>
            
            <!-- PFsense Status -->
            <div class="card bg-gray-800 rounded-lg p-6 shadow-lg">
                <h2 class="text-xl font-bold mb-4 flex items-center">
                    <span class="status-dot status-{{ "online" if pfsense.status == "online" else "offline" }} mr-2"></span>
                    🛡️ PFsense Router
                </h2>
                {% if pfsense.status == "online" %}
                <p class="text-sm text-green-400">✓ Online</p>
                {% else %}
                <p class="text-sm text-red-400">✗ Offline or unreachable</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    botvm = get_botvm_status()
    ha = get_homeassistant_status()
    pfsense = get_pfsense_status()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template_string(
        HTML_TEMPLATE,
        botvm=botvm,
        ha=ha,
        pfsense=pfsense,
        timestamp=timestamp
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
