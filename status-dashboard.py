#!/usr/bin/env python3
"""
BotVM Status Dashboard Server
Monitors BotVM, Home Assistant, PFSense and provides a web interface
"""

import subprocess
import json
import requests
from flask import Flask, render_template_string, jsonify, send_from_directory
import os
import paramiko
import concurrent.futures
import threading
import time
CONFIG = {
    'botvm': {'ip': '10.11.0.114', 'hostname': 'BotVM'},


# Configuration - Using Tailscale IPs for remote systems
    'homeassistant': {'ip': '10.11.0.173', 'port': 8123, 'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZDc2MGFjM2U5ZDg0NzUzYWZkNGJmMTAzOTZmODRmZiIsImlhdCI6MTc3NDc1MTQ1MiwiZXhwIjoyMDkwMTExNDUyfQ.8IM5Mew_fVfnIYnX1aw7e7l_mrt4OOuoU9zgSE8H-zI'},
    'TXPFSenseRouter': {'ip': '10.11.0.1'},  # Renamed from pfsense
    'beloitproxmox': {'ip': '100.96.219.118', 'port': 8006, 'type': 'proxmox', 'username': 'root', 'password': 'Rockyrocks1$'},
    'texasproxmox': {'ip': '10.11.0.2', 'port': 8006, 'type': 'proxmox', 'username': 'root', 'password': 'Rockyrocks1$'},
    'beloitha': {'ip': '100.77.215.26', 'port': 8123, 'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMzFhNmE3MzY0N2I0NGZmODMxZGQwYzg3OTJmYzhmZSIsImlhdCI6MTc3NDkxNDMyNywiZXhwIjoyMDkwMjc0MzI3fQ.nkG-8Ef1c2JO0XvzQ-QBe5TmnVa-fDRlXC40XaAN8xk'},
    'beloitorange': {'ip': '100.77.215.26', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'farmpi': {'ip': '100.117.163.3', 'type': 'system', 'username': 'hha', 'password': 'Rockyrocks1$', 'has_docker': True},
    'texasarm': {'ip': '10.11.0.173', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'BeloitOrangePiZero3': {'ip': '100.77.215.26', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'FarmPi2': {'ip': '100.78.211.108', 'type': 'system', 'username': 'hha', 'password': 'Rockyrocks1$', 'has_docker': True},
}

app = Flask(__name__)

# Global store for bandwidth calculation
pfsense_metrics = {
    'last_rx': 0,
    'last_tx': 0,
    'last_time': 0,
    'rx_mbps': 0.0,
    'tx_mbps': 0.0,
    'rx_window': [],
    'tx_window': []
}
WINDOW_SIZE = 4500 # 15 minutes at 0.2s polling

# Global store for system metrics history
system_metrics = {}
SYSTEM_WINDOW_SIZE = 90 # 15 minutes at 10s polling
metrics_lock = threading.Lock()

def bandwidth_worker():
    """High-frequency polling thread for PfSense bandwidth using a persistent SSH connection"""
    global pfsense_metrics
    hostname = CONFIG['TXPFSenseRouter']['ip']
    username = 'root'
    password = 'Rockyrocks1$'
    cmd = 'netstat -i -b -I igc0'
    
    while True:
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, username=username, password=password, timeout=5)
            
            while True:
                stdin, stdout, stderr = client.exec_command(cmd)
                lines = stdout.read().decode().splitlines()
                
                header = None
                data_line = None
                for line in lines:
                    if 'Name' in line and 'Ibytes' in line:
                        header = line.split()
                    elif line.startswith('igc0') and not data_line:
                        data_line = line.split()
                
                if header and data_line:
                    try:
                        rx_idx = header.index('Ibytes')
                        tx_idx = header.index('Obytes')
                        
                        bytes_rx = int(data_line[rx_idx])
                        bytes_tx = int(data_line[tx_idx])
                        
                        now = time.time()
                        with metrics_lock:
                            if pfsense_metrics['last_time'] != 0:
                                dt = now - pfsense_metrics['last_time']
                                # Use a strictly defined window for the delta to prevent spikes
                                if 0.05 < dt < 5.0:
                                    inst_rx = ((bytes_rx - pfsense_metrics['last_rx']) * 8) / 1_000_000 / dt
                                    inst_tx = ((bytes_tx - pfsense_metrics['last_tx']) * 8) / 1_000_000 / dt
                                    
                                    # Floor at 0 and cap at 10Gbps to avoid outlier noise
                                    inst_rx = max(0, min(inst_rx, 10000))
                                    inst_tx = max(0, min(inst_tx, 10000))
                                    
                                    pfsense_metrics['rx_window'].append(inst_rx)
                                    pfsense_metrics['tx_window'].append(inst_tx)
                                    if len(pfsense_metrics['rx_window']) > WINDOW_SIZE:
                                        pfsense_metrics['rx_window'].pop(0)
                                        pfsense_metrics['tx_window'].pop(0)
                                    
                                    pfsense_metrics['rx_mbps'] = sum(pfsense_metrics['rx_window']) / len(pfsense_metrics['rx_window'])
                                    pfsense_metrics['tx_mbps'] = sum(pfsense_metrics['tx_window']) / len(pfsense_metrics['tx_window'])
                            
                            pfsense_metrics['last_rx'] = bytes_rx
                            pfsense_metrics['last_tx'] = bytes_tx
                            pfsense_metrics['last_time'] = now
                    except (ValueError, IndexError):
                        pass
                time.sleep(0.2)
        except Exception as e:
            print(f"Bandwidth Worker SSH Error: {e}")
            time.sleep(5)
        finally:
            if client:
                client.close()


# Start the bandwidth worker thread
threading.Thread(target=bandwidth_worker, daemon=True).start()

# HA Area Cache
ha_area_cache = {
    'data': {},
    'expiry': 0
}
CACHE_TTL = 1800 # 30 minutes

# Configuration - Using Tailscale IPs for remote systems
CONFIG = {
    'botvm': {'ip': '10.11.0.114', 'hostname': 'BotVM'},
    'homeassistant': {'ip': '10.11.0.173', 'port': 8123, 'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZDc2MGFjM2U5ZDg0NzUzYWZkNGJmMTAzOTZmODRmZiIsImlhdCI6MTc3NDc1MTQ1MiwiZXhwIjoyMDkwMTExNDUyfQ.8IM5Mew_fVfnIYnX1aw7e7l_mrt4OOuoU9zgSE8H-zI'},
    'TXPFSenseRouter': {'ip': '10.11.0.1'},  # Renamed from pfsense
    'beloitproxmox': {'ip': '100.96.219.118', 'port': 8006, 'type': 'proxmox', 'username': 'root', 'password': 'Rockyrocks1$'},
    'texasproxmox': {'ip': '10.11.0.2', 'port': 8006, 'type': 'proxmox', 'username': 'root', 'password': 'Rockyrocks1$'},
    'beloitha': {'ip': '100.77.215.26', 'port': 8123, 'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkMzFhNmE3MzY0N2I0NGZmODMxZGQwYzg3OTJmYzhmZSIsImlhdCI6MTc3NDkxNDMyNywiZXhwIjoyMDkwMjc0MzI3fQ.nkG-8Ef1c2JO0XvzQ-QBe5TmnVa-fDRlXC40XaAN8xk'},
    'beloitorange': {'ip': '100.77.215.26', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'farmpi': {'ip': '100.117.163.3', 'type': 'system', 'username': 'hha', 'password': 'Rockyrocks1$'},
    'texasarm': {'ip': '10.11.0.173', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'BeloitOrangePiZero3': {'ip': '100.77.215.26', 'type': 'system', 'username': 'ubuntu', 'password': 'Rockyrocks1$', 'has_docker': True},
    'FarmPi2': {'ip': '100.78.211.108', 'type': 'system', 'username': 'hha', 'password': 'Rockyrocks1$', 'has_docker': True},
}

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hodgson Home Automation Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        h1 { font-size: 2.5em; color: #4fc3f7; text-shadow: 0 0 20px rgba(79,195,247,0.5); }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 15px;
        }
        .refresh-btn:hover { transform: scale(1.05); transition: transform 0.2s; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .card-header h2 { font-size: 1.4em; color: #fff; flex-grow: 1; }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .status-online { background: #4caf50; box-shadow: 0 0 10px #4caf50; }
        .status-offline { background: #f44336; box-shadow: 0 0 10px #f44336; }
        .status-warning { background: #ff9800; box-shadow: 0 0 10px #ff9800; }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #aaa; font-size: 0.9em; }
        .metric-value { color: #4fc3f7; font-weight: 600; }
        .progress-bar {
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            height: 8px;
            margin-top: 8px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
        }
        .progress-cpu { background: linear-gradient(90deg, #667eea, #764ba2); }
        .progress-mem { background: linear-gradient(90deg, #f093fb, #f5576c); }
        .progress-disk { background: linear-gradient(90deg, #4facfe, #00f2fe); }
        .chart-container {
            margin-top: 20px;
            height: 200px;
            width: 100%;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading { animation: pulse 1s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏠 Hodgson Home Automation Dashboard</h1>
            <p style="color: #aaa; margin-top: 10px;">System Monitoring & Health Check</p>
            <button class="refresh-btn" onclick="updateAll()">↻ Refresh All</button>
        </header>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

        <!-- BotVM Status (Combined) -->
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <span id="botvm-status" class="status-indicator status-online"></span>
                    <h2>🖥️ BotVM (10.11.0.114)</h2>
                </div>
                <div id="botvm-content">
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="cpu-percent">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="mem-percent">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="mem-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Disk Usage</span><span class="metric-value" id="disk-percent">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-disk" id="disk-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Load Average</span><span class="metric-value" id="load-avg">--</span></div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
                    <div class="metric"><span class="metric-label">Docker Containers</span><span class="metric-value" id="docker-count">--</span></div>
                    <div id="docker-list"></div>
                </div>
            </div>

            <!-- Home Assistant Status -->
            <div class="card">
                <div class="card-header">
                    <span id="ha-status" class="status-indicator status-online"></span>
                    <h2>🏠 Home Assistant (10.11.0.173)</h2>
                </div>
                <div id="ha-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="ha-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Entities</span><span class="metric-value" id="ha-entities">--</span></div>
                    <div class="metric"><span class="metric-label">Active Devices</span><span class="metric-value" id="ha-devices">--</span></div>
                </div>
            </div>

            <!-- TXPFSenseRouter Status -->
            <div class="card">
                <div class="card-header">
                    <span id="pfs-status" class="status-indicator status-online"></span>
                    <h2>🛡️ TXPFSenseRouter</h2>
                </div>
                <div id="pfs-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="pfs-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">WAN IP</span><span class="metric-value" id="pfs-wan-ip">--</span></div>
                    <div class="chart-container">
                        <canvas id="pfs-chart"></canvas>
                    </div>
                </div>
            </div>

            <!-- TexasServerARM Status -->
            <div class="card">
                <div class="card-header">
                    <span id="texasarm-status" class="status-indicator status-online"></span>
                    <h2>📱 TexasServerArm (10.11.0.173)</h2>
                </div>
                <div id="texasarm-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="texasarm-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="texasarm-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="texasarm-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="texasarm-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="texasarm-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="texasarm-mem-bar" style="width: 0%"></div></div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
                    <div class="metric"><span class="metric-label">Docker Containers</span><span class="metric-value" id="texasarm-docker-count">--</span></div>
                    <div id="texasarm-docker-list"></div>
                </div>
            </div>

            <!-- Beloit Proxmox Status -->
            <div class="card">
                <div class="card-header">
                    <span id="proxmox-status" class="status-indicator status-online"></span>
                    <h2>🔧 BeloitProxMox (Tailscale)</h2>
                </div>
                <div id="proxmox-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="proxmox-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="proxmox-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="proxmox-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="proxmox-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="proxmox-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="proxmox-mem-bar" style="width: 0%"></div></div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
                    <div class="metric"><span class="metric-label">Active VMs</span><span class="metric-value" id="proxmox-vm-count">--</span></div>
                    <div id="proxmox-vm-list"></div>
                </div>
            </div>

            <!-- TexasProxMox Status -->
            <div class="card">
                <div class="card-header">
                    <span id="texasproxmox-status" class="status-indicator status-online"></span>
                    <h2>🔧 TexasProxMox (10.11.0.2)</h2>
                </div>
                <div id="texasproxmox-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="texasproxmox-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="texasproxmox-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="texasproxmox-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="texasproxmox-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="texasproxmox-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="texasproxmox-mem-bar" style="width: 0%"></div></div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
                    <div class="metric"><span class="metric-label">Active VMs</span><span class="metric-value" id="texasproxmox-vm-count">--</span></div>
                    <div id="texasproxmox-vm-list"></div>
                </div>
            </div>

            <!-- Beloit HA Status -->
            <div class="card">
                <div class="card-header">
                    <span id="beloitha-status" class="status-indicator status-online"></span>
                    <h2>🏠 Beloit HA (Tailscale)</h2>
                </div>
                <div id="beloitha-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="beloitha-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Entities</span><span class="metric-value" id="beloitha-entities">--</span></div>
                </div>
            </div>

            <!-- Beloit Orange Pi 5 Status -->
            <div class="card">
                <div class="card-header">
                    <span id="beloitorange-status" class="status-indicator status-online"></span>
                    <h2>🍊 BeloitOrangePi5 (Tailscale)</h2>
                </div>
                <div id="beloitorange-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="beloitorange-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="beloitorange-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="beloitorange-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="beloitorange-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="beloitorange-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="beloitorange-mem-bar" style="width: 0%"></div></div>
                    <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
                    <div class="metric"><span class="metric-label">Docker Containers</span><span class="metric-value" id="beloitorange-docker-count">--</span></div>
                    <div id="beloitorange-docker-list"></div>
                </div>
            </div>

            <!-- Beloit Orange Pi Zero 3 Status -->
            <div class="card">
                <div class="card-header">
                    <span id="opizero-status" class="status-indicator status-online"></span>
                    <h2>🍊 BeloitOrangePiZero3 (Tailscale)</h2>
                </div>
                <div id="opizero-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="opizero-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="opizero-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="opizero-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="opizero-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="opizero-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="opizero-mem-bar" style="width: 0%"></div></div>
                </div>
            </div>

            <!-- FarmPi 2 Status -->
            <div class="card">
                <div class="card-header">
                    <span id="farmpi2-status" class="status-indicator status-online"></span>
                    <h2>🌾 FarmPi2 (Tailscale)</h2>
                </div>
                <div id="farmpi2-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="farmpi2-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="farmpi2-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="farmpi2-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="farmpi2-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="farmpi2-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="farmpi2-mem-bar" style="width: 0%"></div></div>
                </div>
            </div>

            <!-- Beloit Orange Pi Zero 3 Status -->
            <div class="card">
                <div class="card-header">
                    <span id="opizero-status" class="status-indicator status-online"></span>
                    <h2>🍊 BeloitOrangePiZero3 (Tailscale)</h2>
                </div>
                <div id="opizero-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="opizero-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="opizero-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="opizero-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="opizero-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="opizero-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="opizero-mem-bar" style="width: 0%"></div></div>
                </div>
            </div>

            <!-- FarmPi 2 Status -->
            <div class="card">
                <div class="card-header">
                    <span id="farmpi2-status" class="status-indicator status-online"></span>
                    <h2>🌾 FarmPi2 (Tailscale)</h2>
                </div>
                <div id="farmpi2-content">
                    <div class="metric"><span class="metric-label">Status</span><span class="metric-value" id="farmpi2-status-text">--</span></div>
                    <div class="metric"><span class="metric-label">Uptime</span><span class="metric-value" id="farmpi2-uptime">--</span></div>
                    <div class="metric"><span class="metric-label">CPU Usage</span><span class="metric-value" id="farmpi2-cpu">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-cpu" id="farmpi2-cpu-bar" style="width: 0%"></div></div>
                    <div class="metric"><span class="metric-label">Memory Usage</span><span class="metric-value" id="farmpi2-mem">--%</span></div>
                    <div class="progress-bar"><div class="progress-fill progress-mem" id="farmpi2-mem-bar" style="width: 0%"></div></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Request cancellation and state management
        let currentAbortController = null;
        let lastSuccessfulUpdate = Date.now();
        let updateInProgress = false;
        
        async function updateAll() {
            // Cancel any pending request before starting new one
            if (currentAbortController) {
                try { currentAbortController.abort(); } catch(e) {}
            }
            currentAbortController = new AbortController();
            const signal = currentAbortController.signal;
            
            // Prevent overlapping updates
            if (updateInProgress) return;
            updateInProgress = true;
            
            try {
                const response = await fetch('/api/status', { signal });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                
                // BotVM Status (Combined)
                if (data.botvm) {
                    document.getElementById('uptime').textContent = data.botvm.uptime || '--';
                    document.getElementById('cpu-percent').textContent = `${data.botvm.cpu}%`;
                    document.getElementById('cpu-bar').style.width = `${Math.min(data.botvm.cpu, 100)}%`;
                    document.getElementById('mem-percent').textContent = `${data.botvm.memory}%`;
                    document.getElementById('mem-bar').style.width = `${Math.min(data.botvm.memory, 100)}%`;
                    document.getElementById('disk-percent').textContent = `${data.botvm.disk}%`;
                    document.getElementById('disk-bar').style.width = `${Math.min(data.botvm.disk, 100)}%`;
                    document.getElementById('load-avg').textContent = data.botvm.load_avg || '--';
                    if (data.docker) {
                        document.getElementById('docker-count').textContent = data.docker.count;
                        const listDiv = document.getElementById('docker-list');
                        listDiv.innerHTML = '';
                        data.docker.containers.forEach(c => {
                            const div = document.createElement('div');
                            div.className = 'metric';
                            div.innerHTML = `<span class="metric-label">${c.name}</span><span class="metric-value">${c.status}</span>`;
                            listDiv.appendChild(div);
                        });
                    }
                }

                // Home Assistant Status
                if (data.homeassistant) {
                    const ha = data.homeassistant;
                    document.getElementById('ha-status-text').textContent = ha.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('ha-status').className = `status-indicator status-${ha.online ? 'online' : 'offline'}`;
                    document.getElementById('ha-entities').textContent = ha.entities || '--';
                    document.getElementById('ha-devices').textContent = ha.active_devices || '--';
                }

                // TXPFSenseRouter Status
                if (data.TXPFSenseRouter) {
                    const pfs = data.TXPFSenseRouter;
                    document.getElementById('pfs-status-text').textContent = pfs.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('pfs-status').className = `status-indicator status-${pfs.online ? 'online' : 'offline'}`;
                    document.getElementById('pfs-wan-ip').textContent = pfs.wan_ip || '--';
                    
                    // Update bandwidth and chart if present
                    if (pfs.rx_mbps !== undefined) {
                        const contentDiv = document.getElementById('pfs-content');
                        if (!document.getElementById('pfs-rx')) {
                            contentDiv.innerHTML += `
                                <div class="metric"><span class="metric-label">Download</span><span class="metric-value" id="pfs-rx">--</span></div>
                                <div class="metric"><span class="metric-label">Upload</span><span class="metric-value" id="pfs-tx">--</span></div>
                            `;
                        }
                        document.getElementById('pfs-rx').textContent = `${pfs.rx_mbps} Mbps`;
                        document.getElementById('pfs-tx').textContent = `${pfs.tx_mbps} Mbps`;

                        if (pfs.rx_history) {
                            if (!window.pfsChart) {
                                const ctx = document.getElementById('pfs-chart').getContext('2d');
                                window.pfsChart = new Chart(ctx, {
                                    type: 'line',
                                    data: {
                                        labels: Array.from({length: pfs.rx_history.length}, (_, i) => i),
                                        datasets: [
                                            { label: 'RX Mbps', data: pfs.rx_history, borderColor: '#4fc3f7', tension: 0.1, pointRadius: 0, borderWidth: 2 },
                                            { label: 'TX Mbps', data: pfs.tx_history, borderColor: '#764ba2', tension: 0.1, pointRadius: 0, borderWidth: 2 }
                                        ]
                                    },
                                    options: { 
                                        responsive: true, 
                                        maintainAspectRatio: false, 
                                        animation: false,
                                        scales: { 
                                            x: { display: false }, 
                                            y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#aaa' } } 
                                        },
                                        plugins: { legend: { labels: { color: '#eee' } } }
                                    }
                                });
                            } else {
                                window.pfsChart.data.labels = Array.from({length: pfs.rx_history.length}, (_, i) => i);
                                window.pfsChart.data.datasets[0].data = pfs.rx_history;
                                window.pfsChart.data.datasets[1].data = pfs.tx_history;
                                window.pfsChart.update('none');
                            }
                        }
                    }
                }

                // TexasServerARM Status
                if (data.texasarm) {
                    const arm = data.texasarm;
                    document.getElementById('texasarm-status-text').textContent = arm.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('texasarm-status').className = `status-indicator status-${arm.online ? 'online' : 'offline'}`;
                    if (arm.uptime) {
                        document.getElementById('texasarm-uptime').textContent = arm.uptime;
                    }
                    if (arm.cpu !== undefined) {
                        document.getElementById('texasarm-cpu').textContent = `${arm.cpu}%`;
                        document.getElementById('texasarm-cpu-bar').style.width = `${Math.min(arm.cpu, 100)}%`;
                    }
                    if (arm.memory !== undefined) {
                        document.getElementById('texasarm-mem').textContent = `${arm.memory}%`;
                        document.getElementById('texasarm-mem-bar').style.width = `${Math.min(arm.memory, 100)}%`;
                    }
                    if (arm.docker_count !== undefined) {
                        document.getElementById('texasarm-docker-count').textContent = arm.docker_count;
                    }
                    const dockerListDiv = document.getElementById('texasarm-docker-list');
                    dockerListDiv.innerHTML = '';
                    if (arm.docker_containers && arm.docker_containers.length > 0) {
                        arm.docker_containers.forEach(c => {
                            const div = document.createElement('div');
                            div.className = 'metric';
                            div.innerHTML = `<span class="metric-label">${c.name}</span><span class="metric-value">${c.status}</span>`;
                            dockerListDiv.appendChild(div);
                        });
                    }
                }

                // Beloit Proxmox Status
                if (data.beloitproxmox) {
                    const px = data.beloitproxmox;
                    document.getElementById('proxmox-status-text').textContent = px.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('proxmox-status').className = `status-indicator status-${px.online ? 'online' : 'offline'}`;
                    if (px.uptime) {
                        document.getElementById('proxmox-uptime').textContent = px.uptime;
                    }
                    if (px.cpu !== undefined) {
                        document.getElementById('proxmox-cpu').textContent = `${px.cpu}%`;
                        document.getElementById('proxmox-cpu-bar').style.width = `${Math.min(px.cpu, 100)}%`;
                    }
                    if (px.memory !== undefined) {
                        document.getElementById('proxmox-mem').textContent = `${px.memory}%`;
                        document.getElementById('proxmox-mem-bar').style.width = `${Math.min(px.memory, 100)}%`;
                    }
                    if (px.vm_count !== undefined) {
                        document.getElementById('proxmox-vm-count').textContent = px.vm_count;
                    }
                    const vmListDiv = document.getElementById('proxmox-vm-list');
                    vmListDiv.innerHTML = '';
                    if (px.vms && px.vms.length > 0) {
                        px.vms.forEach(vm => {
                            const div = document.createElement('div');
                            div.className = 'metric';
                            div.innerHTML = `<span class="metric-label">VM ${vm.vmid}</span><span class="metric-value">${vm.name}</span>`;
                            vmListDiv.appendChild(div);
                        });
                    }
                }

                // TexasProxMox Status
                if (data.texasproxmox) {
                    const txpx = data.texasproxmox;
                    document.getElementById('texasproxmox-status-text').textContent = txpx.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('texasproxmox-status').className = `status-indicator status-${txpx.online ? 'online' : 'offline'}`;
                    if (txpx.uptime) {
                        document.getElementById('texasproxmox-uptime').textContent = txpx.uptime;
                    }
                    if (txpx.cpu !== undefined) {
                        document.getElementById('texasproxmox-cpu').textContent = `${txpx.cpu}%`;
                        document.getElementById('texasproxmox-cpu-bar').style.width = `${Math.min(txpx.cpu, 100)}%`;
                    }
                    if (txpx.memory !== undefined) {
                        document.getElementById('texasproxmox-mem').textContent = `${txpx.memory}%`;
                        document.getElementById('texasproxmox-mem-bar').style.width = `${Math.min(txpx.memory, 100)}%`;
                    }
                    if (txpx.vm_count !== undefined) {
                        document.getElementById('texasproxmox-vm-count').textContent = txpx.vm_count;
                    }
                    const vmListDiv = document.getElementById('texasproxmox-vm-list');
                    vmListDiv.innerHTML = '';
                    if (txpx.vms && txpx.vms.length > 0) {
                        txpx.vms.forEach(vm => {
                            const div = document.createElement('div');
                            div.className = 'metric';
                            div.innerHTML = `<span class="metric-label">VM ${vm.vmid}</span><span class="metric-value">${vm.name}</span>`;
                            vmListDiv.appendChild(div);
                        });
                    }
                }

                // Beloit HA Status
                if (data.beloitha) {
                    const bha = data.beloitha;
                    document.getElementById('beloitha-status-text').textContent = bha.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('beloitha-status').className = `status-indicator status-${bha.online ? 'online' : 'offline'}`;
                    document.getElementById('beloitha-entities').textContent = bha.entities || '--';
                }

                // Beloit Orange Pi 5 Status
                if (data.beloitorange) {
                    const orange = data.beloitorange;
                    document.getElementById('beloitorange-status-text').textContent = orange.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('beloitorange-status').className = `status-indicator status-${orange.online ? 'online' : 'offline'}`;
                    if (orange.uptime) {
                        document.getElementById('beloitorange-uptime').textContent = orange.uptime;
                    }
                    if (orange.cpu !== undefined) {
                        document.getElementById('beloitorange-cpu').textContent = `${orange.cpu}%`;
                        document.getElementById('beloitorange-cpu-bar').style.width = `${Math.min(orange.cpu, 100)}%`;
                    }
                    if (orange.memory !== undefined) {
                        document.getElementById('beloitorange-mem').textContent = `${orange.memory}%`;
                        document.getElementById('beloitorange-mem-bar').style.width = `${Math.min(orange.memory, 100)}%`;
                    }
                    if (orange.docker_count !== undefined) {
                        document.getElementById('beloitorange-docker-count').textContent = orange.docker_count;
                    }
                    const dockerListDiv = document.getElementById('beloitorange-docker-list');
                    dockerListDiv.innerHTML = '';
                    if (orange.docker_containers && orange.docker_containers.length > 0) {
                        orange.docker_containers.forEach(c => {
                            const div = document.createElement('div');
                            div.className = 'metric';
                            div.innerHTML = `<span class="metric-label">${c.name}</span><span class="metric-value">${c.status}</span>`;
                            dockerListDiv.appendChild(div);
                        });
                    }
                }

                // Beloit Orange Pi Zero 3 Status
                if (data.BeloitOrangePiZero3) {
                    const opizero = data.BeloitOrangePiZero3;
                    document.getElementById('opizero-status-text').textContent = opizero.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('opizero-status').className = `status-indicator status-${opizero.online ? 'online' : 'offline'}`;
                    if (opizero.uptime) {
                        document.getElementById('opizero-uptime').textContent = opizero.uptime;
                    }
                    if (opizero.cpu !== undefined) {
                        document.getElementById('opizero-cpu').textContent = `${opizero.cpu}%`;
                        document.getElementById('opizero-cpu-bar').style.width = `${Math.min(opizero.cpu, 100)}%`;
                    }
                    if (opizero.memory !== undefined) {
                        document.getElementById('opizero-mem').textContent = `${opizero.memory}%`;
                        document.getElementById('opizero-mem-bar').style.width = `${Math.min(opizero.memory, 100)}%`;
                    }
                }

                // FarmPi 2 Status
                if (data.FarmPi2) {
                    const farm2 = data.FarmPi2;
                    document.getElementById('farmpi2-status-text').textContent = farm2.online ? '✅ Online' : '❌ Offline';
                    document.getElementById('farmpi2-status').className = `status-indicator status-${farm2.online ? 'online' : 'offline'}`;
                    if (farm2.uptime) {
                        document.getElementById('farmpi2-uptime').textContent = farm2.uptime;
                    }
                    if (farm2.cpu !== undefined) {
                        document.getElementById('farmpi2-cpu').textContent = `${farm2.cpu}%`;
                        document.getElementById('farmpi2-cpu-bar').style.width = `${Math.min(farm2.cpu, 100)}%`;
                    }
                    if (farm2.memory !== undefined) {
                        document.getElementById('farmpi2-mem').textContent = `${farm2.memory}%`;
                        document.getElementById('farmpi2-mem-bar').style.width = `${Math.min(farm2.memory, 100)}%`;
                    }
                }
            } catch (e) {
                    // Only log errors that aren't aborts or network issues
                    if (e.name !== 'AbortError' && e.name !== 'TypeError') {
                        console.error('Update error:', e);
                    }
                    updateInProgress = false;
                    return;
                } finally {
                    updateInProgress = false;
                }
        }

        // Initial load and auto-refresh every 10 seconds
        updateAll();
        setInterval(updateAll, 10000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    # Use absolute path to static directory
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, 'index.html')

@app.route('/api/status')
def get_status():
    status = {}
    
    # Thread-safe cache for concurrent fetching
    cache_lock = threading.Lock()
    cached_status = {}
    
    def fetch_botvm_local():
        """Fetch local BotVM metrics"""
        data = {'uptime': '--', 'cpu': 0, 'memory': 0, 'disk': 0, 'load_avg': '--'}
        try:
            result = subprocess.run(['uptime', '-s'], capture_output=True, text=True)
            uptime_start = result.stdout.strip()
            from datetime import datetime
            start_time = datetime.strptime(uptime_start, '%Y-%m-%d %H:%M')
            uptime_seconds = int((datetime.now() - start_time).total_seconds())
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            data['uptime'] = f'{days}d {hours}h'
        except: pass
        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[:3]
                data['load_avg'] = ', '.join(load_avg)
        except: pass
        try:
            def get_cpu_usage():
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                values = line.split()[1:8]
                values = [int(v) for v in values]
                idle = values[3]
                total = sum(values)
                return 100 - (idle * 100 // total)
            import time
            cpu1 = get_cpu_usage()
            time.sleep(0.5)
            cpu2 = get_cpu_usage()
            data['cpu'] = max(cpu1, cpu2)
        except: pass
        try:
            result = subprocess.run(['free', '-m'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            mem_parts = lines[1].split()
            total_mem = int(mem_parts[1])
            used_mem = int(mem_parts[2])
            data['memory'] = (used_mem * 100 // total_mem)
        except: pass
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            disk_parts = lines[1].split()
            data['disk'] = int(disk_parts[4].replace('%', ''))
        except: pass

        # Update History
        with metrics_lock:
            if 'botvm' not in system_metrics:
                system_metrics['botvm'] = {'cpu': [], 'memory': [], 'disk': []}
            system_metrics['botvm']['cpu'].append(data['cpu'])
            system_metrics['botvm']['memory'].append(data['memory'])
            system_metrics['botvm']['disk'].append(data['disk'])
            if len(system_metrics['botvm']['cpu']) > SYSTEM_WINDOW_SIZE:
                system_metrics['botvm']['cpu'].pop(0)
            if len(system_metrics['botvm']['memory']) > SYSTEM_WINDOW_SIZE:
                system_metrics['botvm']['memory'].pop(0)
            if len(system_metrics['botvm']['disk']) > SYSTEM_WINDOW_SIZE:
                system_metrics['botvm']['disk'].pop(0)
        
        return data
    
    def fetch_homeassistant():
        """Fetch Home Assistant status"""
        try:
            headers = {'Authorization': f'Bearer {CONFIG["homeassistant"]["token"]}'} if CONFIG['homeassistant']['token'] else {}
            response = requests.get(f'http://{CONFIG["homeassistant"]["ip"]}:{CONFIG["homeassistant"]["port"]}/api/states', headers=headers, timeout=3)
            entities = response.json()
            active_devices = len([e for e in entities if e['state'] == 'on' or e['state'] != 'off'])
            return {'online': True, 'entities': len(entities), 'active_devices': active_devices}
        except:
            return {'online': False}

    def fetch_ha_area_map():
        """Fetch Area -> Entity mapping using HA template API with 30m cache"""
        global ha_area_cache
        now = time.time()
        if ha_area_cache['data'] and now < ha_area_cache['expiry']:
            return ha_area_cache['data']

        try:
            token = CONFIG['homeassistant']['token']
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            # Avoid using .update() or other prohibited dict methods to bypass SecurityError
            template = """
            {% for state in states %}
              {% set area = area_name(state.entity_id) %}
              {% if area %}
                {{ area }}|{{ state.entity_id }}\n
              {% endif %}
            {% endfor %}
            """
            payload = {"template": template}
            response = requests.post(
                f"http://{CONFIG['homeassistant']['ip']}:{CONFIG['homeassistant']['port']}/api/template",
                headers=headers, json=payload, timeout=5
            )
            
            mapping = {}
            lines = response.text.strip().split('\n')
            for line in lines:
                if '|' in line:
                    area, eid = line.split('|', 1)
                    if area not in mapping:
                        mapping[area] = []
                    mapping[area].append(eid)
            
            ha_area_cache['data'] = mapping
            ha_area_cache['expiry'] = now + CACHE_TTL
            return mapping
        except Exception as e:
            print(f"HA Area Map Error: {e}")
            return {}
    
    def fetch_pfsense():
        """Fetch PFSense status and live bandwidth"""
        try:
            # Check online status via ping
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', CONFIG['TXPFSenseRouter']['ip']], capture_output=True, text=True)
            if ping_result.returncode != 0:
                return {'online': False}
            
            # We rely on the bandwidth_worker thread for real-time Mbps.
            # We just need the WAN IP and online status here.
            password = 'Rockyrocks1$' 
            ip_result = subprocess.run(['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no', 'root@10.11.0.1', 'curl -s https://ifconfig.me'], capture_output=True, text=True, timeout=5)
            wan_ip = ip_result.stdout.strip()

            with metrics_lock:
                rx_mbps = pfsense_metrics['rx_mbps']
                tx_mbps = pfsense_metrics['tx_mbps']
                rx_history = pfsense_metrics['rx_window'][:]
                tx_history = pfsense_metrics['tx_window'][:]

            return {
                'online': True, 
                'wan_ip': wan_ip, 
                'rx_mbps': round(max(0, rx_mbps), 2), 
                'tx_mbps': round(max(0, tx_mbps), 2),
                'rx_history': rx_history,
                'tx_history': tx_history
            }
        except Exception as e:
            return {'online': False, 'error': str(e)}
    
    def fetch_docker():
        """Fetch Docker containers on BotVM"""
        try:
            result = subprocess.run(['curl', '-s', '--unix', '/var/run/docker.sock', 'http://localhost/containers/json'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                containers = json.loads(result.stdout)
                return {
                    'count': len(containers),
                    'containers': [{'name': c.get('Names', ['unknown'])[0].replace('/', ''), 'status': c.get('Status', '--')} for c in containers]
                }
        except: pass
        return {'count': 0, 'containers': []}
    
    def fetch_ssh_system(system_key, config):
        """Generic SSH system fetcher"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(config['ip'], username=config['username'], password=config['password'], timeout=5)
            data = {'online': True}
            
            # Get Uptime - use -p for pretty format, avoid date parsing
            stdin, stdout, stderr = client.exec_command('uptime -p')
            data['uptime'] = stdout.read().decode().strip()
            
            # Get CPU - use load average as a proxy
            stdin, stdout, stderr = client.exec_command('cat /proc/loadavg')
            load_line = stdout.read().decode().strip()
            load_parts = load_line.split()
            if len(load_parts) >= 1:
                data['cpu'] = min(int(float(load_parts[0]) * 25), 100)
            
            # Get Memory
            stdin, stdout, stderr = client.exec_command('free | grep Mem')
            mem_line = stdout.read().decode().strip()
            mem_parts = mem_line.split()
            if len(mem_parts) >= 3:
                data['memory'] = (int(mem_parts[2]) * 100 // int(mem_parts[1]))
            
            # Update History
            with metrics_lock:
                if system_key not in system_metrics:
                    system_metrics[system_key] = {'cpu': [], 'memory': []}
                system_metrics[system_key]['cpu'].append(data.get('cpu', 0))
                system_metrics[system_key]['memory'].append(data.get('memory', 0))
                if len(system_metrics[system_key]['cpu']) > SYSTEM_WINDOW_SIZE:
                    system_metrics[system_key]['cpu'].pop(0)
                if len(system_metrics[system_key]['memory']) > SYSTEM_WINDOW_SIZE:
                    system_metrics[system_key]['memory'].pop(0)

            # Docker containers if requested
            if config.get('has_docker'):
                stdin, stdout, stderr = client.exec_command('docker ps --format "{{.Names}}\t{{.Status}}"')
                containers_output = stdout.read().decode().strip()
                if containers_output:
                    container_list = []
                    for line in containers_output.split('\n'):
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            container_list.append({'name': parts[0], 'status': parts[1]})
                    data['docker_count'] = len(container_list)
                    data['docker_containers'] = container_list
            
            # Proxmox VMs if requested
            if config.get('type') == 'proxmox':
                stdin, stdout, stderr = client.exec_command('qm list | grep running')
                vms_output = stdout.read().decode().strip()
                if vms_output:
                    vm_list = []
                    for line in vms_output.split('\n'):
                        parts = line.split()
                        if len(parts) >= 3:
                            vm_list.append({'vmid': parts[0], 'name': parts[1], 'cpu': 0, 'memory': 0})
                    data['vms'] = vm_list
                    data['vm_count'] = len(vm_list)
            
            client.close()
            return data
        except Exception as e:
            print(f"SSH Error ({system_key}): {e}")
            return {'online': False}
    
    def fetch_beloitproxmox():
        return fetch_ssh_system('beloitproxmox', CONFIG['beloitproxmox'])
    
    def fetch_texasarm():
        return fetch_ssh_system('texasarm', CONFIG['texasarm'])
    
    def fetch_texasproxmox():
        return fetch_ssh_system('texasproxmox', CONFIG['texasproxmox'])
    
    def fetch_beloitorange():
        return fetch_ssh_system('beloitorange', CONFIG['beloitorange'])
    
    def fetch_farmpi():
        return fetch_ssh_system('farmpi', CONFIG['farmpi'])
    
    def fetch_beloitopizero3():
        return fetch_ssh_system('BeloitOrangePiZero3', CONFIG['BeloitOrangePiZero3'])
    
    def fetch_farmpi2():
        return fetch_ssh_system('FarmPi2', CONFIG['FarmPi2'])
    
    def fetch_beloitha():
        """Fetch Beloit HA status"""
        try:
            headers = {'Authorization': f'Bearer {CONFIG["beloitha"]["token"]}'} if CONFIG['beloitha']['token'] else {}
            response = requests.get(f'http://{CONFIG["beloitha"]["ip"]}:{CONFIG["beloitha"]["port"]}/api/states', headers=headers, timeout=3)
            entities = response.json()
            return {'online': True, 'entities': len(entities)}
        except:
            return {'online': False}
    
    # Execute all fetches concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_botvm_local): 'botvm',
            executor.submit(fetch_homeassistant): 'homeassistant',
            executor.submit(fetch_pfsense): 'TXPFSenseRouter',
            executor.submit(fetch_docker): 'docker',
            executor.submit(fetch_beloitproxmox): 'beloitproxmox',
            executor.submit(fetch_texasarm): 'texasarm',
            executor.submit(fetch_texasproxmox): 'texasproxmox',
            executor.submit(fetch_beloitorange): 'beloitorange',
            executor.submit(fetch_farmpi): 'farmpi',
            executor.submit(fetch_beloitopizero3): 'BeloitOrangePiZero3',
            executor.submit(fetch_farmpi2): 'FarmPi2',
            executor.submit(fetch_beloitha): 'beloitha',
            executor.submit(fetch_ha_area_map): 'ha_area_map',
        }
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                result = future.result()
                with cache_lock:
                    cached_status[key] = result
            except Exception as e:
                with cache_lock:
                    cached_status[key] = {'online': False}
    
    # Merge cached results into status
    with cache_lock:
        for key, value in cached_status.items():
            if key == 'docker' and value.get('count', 0) > 0:
                status['docker'] = value
            elif key == 'ha_area_map':
                # Optimization: Send only area names and counts to avoid frontend data-bombs
                # Full map is available via separate API if needed
                summary_areas = {area: len(entities) for area, entities in value.items()}
                status['ha_areas_summary'] = summary_areas
            elif key != 'docker':
                # Inject history for any system that has it
                if key in system_metrics:
                    value['cpu_history'] = system_metrics[key]['cpu']
                    value['memory_history'] = system_metrics[key]['memory']
                status[key] = value
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
