#!/usr/bin/env python3
import paramiko

def get_txserverarm_stats():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('10.11.0.173', username='ubuntu', password='Rockyrocks1$', timeout=5)
        
        # Get uptime
        stdin, stdout, stderr = client.exec_command('uptime -p')
        uptime = stdout.read().decode().strip()
        print(f"Uptime:   {uptime}")
        
        # Get memory
        stdin2, stdout2, stderr2 = client.exec_command('free | grep Mem')
        mem_line = stdout2.read().decode().strip()
        parts = mem_line.split()
        if len(parts) >= 3:
            mem_used = int(parts[2])
            mem_total = int(parts[1])
            mem_pct = (mem_used * 100 // mem_total)
            print(f"Memory:   {mem_used}K/{mem_total}K ({mem_pct}% used)")
        
        # Get docker containers
        stdin3, stdout3, stderr3 = client.exec_command('docker ps --format "{{.Names}}\t{{.Status}}"')
        containers = stdout3.read().decode().strip()
        if containers:
            print(f"\nDocker Containers (TxServerArm):")
            for line in containers.split('\n'):
                print(f"  {line}")
        
        client.close()
    except Exception as e:
        print(f"Error connecting to TxServerArm: {e}")

if __name__ == "__main__":
    get_txserverarm_stats()
