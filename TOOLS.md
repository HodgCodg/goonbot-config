# TOOLS.md — Infrastructure Reference

## BotVM (this host: 10.11.0.114)
- CPU: Intel 12600K | GPU: RTX 3060 Ti | OS: Ubuntu | RAM: 16GB
- OpenClaw: systemd user service openclaw-gateway, port 18789
- Caddy HTTPS: systemd service caddy-openclaw, port 18790
- SSH Tool API: port 7722, systemd service ssh-tool
- Docker: searxng (:8888), ollama (:11434), clawdbot/Open WebUI (:8080)

## Zach's PC (10.11.0.132)
- GPU: RX 9070 XT (16GB VRAM)
- LM Studio: port 1234, serving Qwen3.5-27B Claude-distilled

## Networking
- Tailscale for cross-site
- Proxmox hypervisor: 10.11.0.2:8006 (VM 102 = BotVM)
- Beloit site: Xeon E-2144G, Blue Iris NVR

## Smart Home (10.11.0.173)
- Home Assistant: port 8123, REST API, long-lived access token
- UniFi Network Controller: port 8443, HTTPS, login-based auth

## Installed Skills
weather, searxng, fetch, calc, sysinfo, docker, network, self, ssh, code, chatgpt, homeassistant, unifi

## Execution Model
To run commands on BotVM, use the **exec** tool (NOT the process tool).
- `exec` takes a `command` string and runs it on the gateway host (BotVM)
- Example: exec with command="uptime" returns the system uptime
- The `process` tool is for managing already-running background sessions only
- All skill commands in the table below should be called via exec

## Parallel Execution (Subagents)
You can spawn up to 3 concurrent subagents for independent parallel workstreams.

To spawn a subagent: use the sessions_spawn tool with runtime set to subagent and a task string describing what to do.
Each subagent runs independently. Use sessions_yield to wait for it to finish and retrieve the result.
Use the subagents tool (action: list / steer / kill) to manage running agents.

When to use subagents:
- Multiple devices to update simultaneously (ssh into 3 hosts at once)
- Independent research + file work in parallel
- Any task where workstreams do NOT depend on each other

When NOT to use subagents:
- Tasks that must be sequential (step 2 needs step 1 result)
- Simple one-step tasks (overhead not worth it)
- Tasks writing to the same file (race condition)

Limit: maxConcurrent = 3. Do not spawn more than 3 subagents at once.

## Exec Command Restrictions
**Compound commands are blocked by exec preflight.** These operators will fail:
- `&&` — chain commands
- `||` — fallback commands  
- `&` — background execution
- Pipe chains like `cmd1 | cmd2` may also be restricted

Instead, split into separate exec calls:
```
# WRONG (fails):
exec: kill 12345 && python3 app.py

# CORRECT (two calls):
exec: kill 12345
exec: python3 app.py
```

To run a background process: use `nohup python3 app.py > /tmp/app.log 2>&1` (single command, no &&).
