#!/usr/bin/env python3
"""
Long-Term Memory Skill for OpenClaw
Persistent memory storage with recall, auto-store, and context compaction.
"""

import json
import uuid
import argparse
import os
from datetime import datetime
from pathlib import Path
import re

# Configuration
WORKSPACE = Path("/home/botvm/.openclaw/workspace")
SKILL_DIR = WORKSPACE / "skills" / "longterm-memory"
DATA_FILE = SKILL_DIR / "data" / "memories.jsonl"

# Ensure directories exist
SKILL_DIR.mkdir(parents=True, exist_ok=True)
(SKILL_DIR / "data").mkdir(exist_ok=True)
(SKILL_DIR / "scripts").mkdir(exist_ok=True)

# Initialize data file if it doesn't exist
if not DATA_FILE.exists():
    DATA_FILE.touch()


def generate_id():
    return str(uuid.uuid4())[:8]


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


def load_memories():
    """Load all memories from JSONL file."""
    memories = []
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return memories


def save_memory(memory):
    """Append a single memory to the JSONL file."""
    with open(DATA_FILE, 'a') as f:
        f.write(json.dumps(memory) + '\n')


def cmd_store(args):
    """Store a new memory entry."""
    memory = {
        "id": generate_id(),
        "timestamp": now_iso(),
        "type": args.type or "fact",
        "content": args.text,
        "tags": args.tags.split(',') if args.tags else [],
        "priority": args.priority or 3,
        "source": args.source or "user"
    }
    save_memory(memory)
    print(f"✓ Stored memory [{memory['id']}]: {args.text[:60]}...")


def cmd_auto(args):
    """Auto-store important information (agent-initiated)."""
    memory = {
        "id": generate_id(),
        "timestamp": now_iso(),
        "type": "auto",
        "content": args.text,
        "tags": args.tags.split(',') if args.tags else [],
        "priority": args.priority or 3,
        "source": "agent"
    }
    save_memory(memory)
    # Minimal output for agent use
    print(f"[{memory['id']}] {args.text[:50]}...")


def cmd_recall(args):
    """Search and recall memories."""
    memories = load_memories()
    
    # Filter by query text (search in content and tags)
    if args.query:
        query_lower = args.query.lower()
        filtered = []
        for m in memories:
            content_match = query_lower in m.get("content", "").lower()
            tag_match = any(query_lower in tag.lower() for tag in m.get("tags", []))
            if content_match or tag_match:
                filtered.append(m)
        memories = filtered
    
    # Filter by type
    if args.type:
        memories = [m for m in memories if m.get("type") == args.type]
    
    # Filter by priority range
    if args.min_priority:
        memories = [m for m in memories if m.get("priority", 1) >= args.min_priority]
    
    # Sort by timestamp descending (newest first)
    memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Limit results
    limit = args.limit or 10
    memories = memories[:limit]
    
    if not memories:
        print("No matching memories found.")
        return
    
    # Output
    for m in memories:
        tags_str = f" [{', '.join(m.get('tags', []))}]" if m.get('tags') else ""
        priority_str = f" P{m.get('priority', 3)}" if args.show_priority else ""
        print(f"[{m['id']}] {m['timestamp']} | {m.get('type', 'fact')}|{m.get('source', '')}{priority_str}{tags_str}")
        print(f"    {m.get('content', '')}")
        print()


def cmd_list(args):
    """List recent memories."""
    memories = load_memories()
    memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    limit = args.limit or 10
    memories = memories[:limit]
    
    if not memories:
        print("No memories stored yet.")
        return
    
    for m in memories:
        tags_str = f" [{', '.join(m.get('tags', []))}]" if m.get('tags') else ""
        print(f"[{m['id']}] {m['timestamp']} | {m.get('type')}|{m.get('source')}{tags_str}")
        print(f"    {m.get('content', '')[:100]}..." if len(m.get('content','')) > 100 else f"    {m.get('content', '')}")


def cmd_get(args):
    """Get a specific memory by ID."""
    memories = load_memories()
    for m in memories:
        if m.get("id") == args.id:
            print(f"ID: {m['id']}")
            print(f"Timestamp: {m['timestamp']}")
            print(f"Type: {m['type']}")
            print(f"Source: {m['source']}")
            print(f"Priority: {m.get('priority', 3)}")
            print(f"Tags: {', '.join(m.get('tags', []))}")
            print(f"Content:\n{m['content']}")
            return
    print(f"Memory not found: {args.id}")


def cmd_compact(args):
    """Context compaction - summarize a range of context into LTM."""
    # This is meant to be called by the agent with summary text
    if not args.summary:
        print("Error: --summary required. Provide the text to compact into memory.")
        return
    
    memory = {
        "id": generate_id(),
        "timestamp": now_iso(),
        "type": "compact",
        "content": args.summary,
        "tags": args.tags.split(',') if args.tags else ["compacted"],
        "priority": args.priority or 2,
        "source": "agent"
    }
    save_memory(memory)
    print(f"✓ Compacted into memory [{memory['id']}]")
    print(f"    {args.summary[:80]}...")


def cmd_status(args):
    """Show memory statistics."""
    memories = load_memories()
    
    total = len(memories)
    size_bytes = DATA_FILE.stat().st_size if DATA_FILE.exists() else 0
    
    # Count by type
    by_type = {}
    for m in memories:
        t = m.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    
    print(f"🧠 Long-Term Memory Status")
    print(f"  Total entries: {total}")
    print(f"  Storage size: {size_bytes:,} bytes")
    print(f"  By type:")
    for t, count in sorted(by_type.items()):
        print(f"    • {t}: {count}")
    
    if total > 0:
        oldest = min(memories, key=lambda x: x.get("timestamp", ""))
        newest = max(memories, key=lambda x: x.get("timestamp", ""))
        print(f"  Oldest: {oldest['timestamp']}")
        print(f"  Newest: {newest['timestamp']}")


def cmd_tags(args):
    """List all unique tags."""
    memories = load_memories()
    all_tags = set()
    for m in memories:
        all_tags.update(m.get("tags", []))
    
    if not all_tags:
        print("No tags found.")
        return
    
    print(f"Tags ({len(all_tags)}):")
    for tag in sorted(all_tags):
        count = sum(1 for m in memories if tag in m.get("tags", []))
        print(f"  • {tag}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Long-Term Memory Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Store a memory:
    python3 memory.py store "Zach prefers concise answers" --tags preferences --priority 4
  
  Auto-store (agent use):
    python3 memory.py auto "User mentioned working on project X"
  
  Recall/search:
    python3 memory.py recall "preferences" -n 5
    python3 memory.py list -n 10
  
  Get specific entry:
    python3 memory.py get abc12345
  
  Context compaction:
    python3 memory.py compact --summary "Old conversation summary here"
  
  Status:
    python3 memory.py status
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # STORE command
    store_parser = subparsers.add_parser("store", help="Store a new memory")
    store_parser.add_argument("text", help="Content to store")
    store_parser.add_argument("--type", choices=["fact", "summary", "preference", "event"], default="fact")
    store_parser.add_argument("--tags", help="Comma-separated tags")
    store_parser.add_argument("--priority", type=int, choices=range(1, 6), default=3)
    store_parser.add_argument("--source", choices=["user", "agent"], default="user")
    
    # AUTO command
    auto_parser = subparsers.add_parser("auto", help="Auto-store important info (agent use)")
    auto_parser.add_argument("text", help="Content to store")
    auto_parser.add_argument("--tags", help="Comma-separated tags")
    auto_parser.add_argument("--priority", type=int, choices=range(1, 6), default=3)
    
    # RECALL command
    recall_parser = subparsers.add_parser("recall", help="Search and recall memories")
    recall_parser.add_argument("query", nargs="?", help="Search query")
    recall_parser.add_argument("--type", help="Filter by type")
    recall_parser.add_argument("--min-priority", type=int, choices=range(1, 6))
    recall_parser.add_argument("-n", "--limit", type=int, default=10)
    recall_parser.add_argument("--show-priority", action="store_true")
    
    # LIST command
    list_parser = subparsers.add_parser("list", help="List recent memories")
    list_parser.add_argument("-n", "--limit", type=int, default=10)
    
    # GET command
    get_parser = subparsers.add_parser("get", help="Get specific memory by ID")
    get_parser.add_argument("id", help="Memory ID")
    
    # COMPACT command
    compact_parser = subparsers.add_parser("compact", help="Context compaction")
    compact_parser.add_argument("--summary", required=True, help="Summary text to store")
    compact_parser.add_argument("--tags", help="Comma-separated tags")
    compact_parser.add_argument("--priority", type=int, choices=range(1, 6), default=2)
    
    # STATUS command
    status_parser = subparsers.add_parser("status", help="Show memory statistics")
    
    # TAGS command
    tags_parser = subparsers.add_parser("tags", help="List all unique tags")
    
    args = parser.parse_args()
    
    if args.command == "store":
        cmd_store(args)
    elif args.command == "auto":
        cmd_auto(args)
    elif args.command == "recall":
        cmd_recall(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "compact":
        cmd_compact(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "tags":
        cmd_tags(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
