# ☢️ GoonBot Config & Toolset

**GoonBot** is an autonomous local AI operator running on OpenClaw. Unlike typical chat-bots, GoonBot is designed for **endurance and execution**—carrying out multi-step technical missions on a local VM (BotVM) with a focus on accuracy, verification, and minimal filler.

This repository contains the operational substrate, custom skills, and system configuration that define GoonBot's behavior and capabilities.

## 🧠 Core Operating Model

GoonBot does not "guess"; it operates via a disciplined pipeline designed to minimize loops and maximize forward progress.

### The Execution Pipeline:
`Triage` $\rightarrow$ `Tiering` $\rightarrow$ `Mission Brief` $\rightarrow$ `Execution` $\rightarrow$ `Verification`

1. **Triage**: Every request is passed through a complexity scorer.
2. **Tiering**: Tasks are assigned a Tier (T1, T2, T3) based on risk and tool depth.
3. **Briefing**: A concrete mission brief is generated, outlining the exact steps and success criteria.
4. **Execution**: Work is performed via `exec` tool calls, prioritizing stability and reversibility.
5. **Verification**: No task is marked "Done" without an independent verification check (e.g., curling an endpoint, reading a log).

---

## 📂 Repository Structure

### 📜 Core Identity & Logic
- **`SOUL.md`**: The primary behavioral directive. Contains the anti-loop rules, tool standards, and operating philosophy.
- **`IDENTITY.md`**: Defines the persona, vibe, and creature type.
- **`TOOLS.md`**: Infrastructure reference for the host environment (BotVM, Proxmox, Home Assistant).
- **`AGENTS.md`**: Routing configuration for specialized sub-agents.
- **`TRIAGE_FLOW.md`**: The standard operating procedure for the tiered routing system.

### 🛠️ Skills & Tooling (`/skills`)
Custom autonomous skills that extend GoonBot's reach:
- **`triage`**: Complexity scoring and mission planning.
- **`status-dashboard`**: A high-performance React/Flask dashboard for real-time system health.
- **`longterm-memory`**: A persistent memory system for tracking preferences and facts across sessions.
- **`homeassistant` / `unifi`**: Direct integration with smart home and network infrastructure.
- **`sports-betting`**: Specialized research and EV calculation tools.
- **`self`**: Tools allowing GoonBot to audit and edit its own configuration.

### 📉 Infrastructure (`/static` & `status-dashboard.py`)
The **System Status Dashboard** provides a real-time view of the home lab:
- **PfSense Integration**: Real-time RX/TX bandwidth tracking with 15-minute history graphs.
- **Proxmox/Linux Monitoring**: CPU, Memory, and Disk usage across multiple sites.
- **Docker Tracking**: Status monitoring for all critical containers.

---

## 🚀 Setup & Usage

This repo is a configuration export. To implement similar logic in an OpenClaw environment:

1. **Deploy the Core**: Add `SOUL.md` and `IDENTITY.md` to your workspace.
2. **Install Skills**: Copy the desired directories from `/skills` to your `.openclaw/workspace/skills` path.
3. **Configure Tools**: Update `TOOLS.md` to reflect your local IP addresses and hardware.
4. **Auth**: Set up necessary API tokens (Home Assistant, GitHub, etc.) in your local secret manager.

## ⚠️ Security Note
**This repository is sanitized.** All API keys, SSH keys, passwords, and personal memory data have been stripped. Never commit raw credentials to a public repository.

---

*Built for efficiency. Optimized for endurance. No fluff, just results.* ☢️
