---
name: homeassistant
description: Control Home Assistant smart home devices (lights, switches, thermostats, locks, scenes, automations).
metadata:
  openclaw:
    emoji: "🏠"
    requires:
      bins:
        - python3
---
# Home Assistant Control

```bash
python3 {baseDir}/scripts/ha.py <command> [args]
```

Commands: areas, area <room>, find <query>, entity <id>, states, turn_on/turn_off/toggle <id>, set <id> brightness=N color_temp=N, room_on/room_off <room>, scene [id], automation [id on|off|trigger], climate [id temp], history <id> [hours], config.

Rules: Use find/areas first if you don't know entity_id. Prefer light.* over switch.*. Use room_on/room_off for whole-room control. Room names use underscores.
