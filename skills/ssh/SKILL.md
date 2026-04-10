# SSH Remote Exec Skill

Execute shell commands on remote SSH hosts via the SSH HTTP API.

## Usage

```bash
python3 /home/botvm/.openclaw/workspace/skills/ssh/scripts/ssh_exec.py "command here"
```

## Options
- Default host: botvm (this machine)
- Use `-H hostname` for other hosts
- Use `-t seconds` for longer timeout (default 120s)
- Use `--list-hosts` to see available hosts

## Examples
```bash
# Check uptime
python3 /home/botvm/.openclaw/workspace/skills/ssh/scripts/ssh_exec.py "uptime"

# Check disk space
python3 /home/botvm/.openclaw/workspace/skills/ssh/scripts/ssh_exec.py "df -h"

# Run apt update (sudo works without password)
python3 /home/botvm/.openclaw/workspace/skills/ssh/scripts/ssh_exec.py "sudo apt update"

# Docker status
python3 /home/botvm/.openclaw/workspace/skills/ssh/scripts/ssh_exec.py "sudo docker ps"
```
