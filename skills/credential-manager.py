import os
import json
import base64
from pathlib import Path
import argparse

VAULT_PATH = Path("/home/botvm/.openclaw/vault/credentials.json")
SECRET_KEY = "goona-vault-key-2026"

def encrypt(text):
    result = []
    for i in range(len(text)):
        result.append(chr(ord(text[i]) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])))
    return base64.b64encode("".join(result).encode()).decode()

def decrypt(token):
    try:
        decoded = base64.b64decode(token).decode()
        result = []
        for i in range(len(decoded)):
            result.append(chr(ord(decoded[i]) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])))
        return "".join(result)
    except Exception:
        return None

def load_vault():
    if not VAULT_PATH.exists():
        return {}
    with open(VAULT_PATH, 'r') as f:
        return json.load(f)

def save_vault(vault):
    with open(VAULT_PATH, 'w') as f:
        json.dump(vault, f, indent=2)

def store(service, username, password=None, key_path=None):
    vault = load_vault()
    vault[service] = {
        "username": username,
        "password": encrypt(password) if password else None,
        "key_path": key_path
    }
    save_vault(vault)
    return f"Stored credentials for {service}."

def get(service):
    vault = load_vault()
    cred = vault.get(service)
    if not cred:
        return None
    
    return {
        "username": cred["username"],
        "password": decrypt(cred["password"]) if cred["password"] else None,
        "key_path": cred["key_path"]
    }

def list_services():
    vault = load_vault()
    return list(vault.keys())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GoonBot Credential Manager")
    subparsers = parser.add_subparsers(dest="command")

    store_p = subparsers.add_parser("store")
    store_p.add_argument("service")
    store_p.add_argument("username")
    store_p.add_argument("--password", default=None)
    store_p.add_argument("--key", default=None)

    get_p = subparsers.add_parser("get")
    get_p.add_argument("service")

    list_p = subparsers.add_parser("list")

    args = parser.parse_args()

    if args.command == "store":
        print(store(args.service, args.username, args.password, args.key))
    elif args.command == "get":
        res = get(args.service)
        if res:
            print(json.dumps(res))
        else:
            print("Not found")
    elif args.command == "list":
        print(", ".join(list_services()))
