#!/usr/bin/env python3
"""
Module: Operator Console
Description: CLI for interacting with the C2 Team Server.
"""

import requests
import sys
import argparse

SERVER_URL = "http://localhost:8080"

def queue_task(agent_id, command):
    """Sends a task to the Team Server."""
    url = f"{SERVER_URL}/admin/queue"
    payload = {"agent_id": agent_id, "command": command}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 201:
            data = response.json()
            print(f"[+] Task {data['task_id']} queued successfully.")
        else:
            print(f"[-] Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("[-] Could not connect to Team Server.")

def main():
    parser = argparse.ArgumentParser(description="C2 Operator Console")
    parser.add_argument("agent_id", help="Target Agent UUID")
    parser.add_argument("command", help="Command to execute (e.g., 'whoami', 'die')")
    
    args = parser.parse_args()
    
    print(f"[*] Targeting Agent: {args.agent_id}")
    queue_task(args.agent_id, args.command)

if __name__ == "__main__":
    main()

    