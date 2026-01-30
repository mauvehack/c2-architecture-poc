# C2 Architecture: Modular Command & Control Framework

**Author:** mauvehack
**Codename:** c2-infrastructure
**Status:** Active Prototype (PoC)
**License:** MIT

---

## **Project Overview**

We are building a ghost.

This repository houses a modular Command and Control (C2) framework designed to simulate advanced post-exploitation tradecraft. In a landscape dominated by noisy reverse shells, this architecture prioritizes **silence** and **resilience**.

The objective is to engineer a communication channel that decouples logic from transport, utilizing asynchronous "malleable" profiles to dissolve into the background noise of legitimate network traffic.

This is a study in persistence.

---

## **System Architecture**

The framework utilizes a distributed client-server model designed for high-latency, hostile environments. It does not maintain a connection; it pulses.

```mermaid
graph LR
    A[Operator Console] -- REST API --> B(Team Server)
    B -- Encrypted Tasking --> C{Listener}
    C -- HTTP/S Heartbeat --> D[Implant / Agent]
    D -- Execution Output --> C
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#bfb,stroke:#333,stroke-width:2px


    ## **Core Components**
    
    #Team Server (Python/Flask):The central nervous system. It manages listener state, queues asynchronous tasks, and persists operational data to a relational database. It never touches the target directly.
    
    #The Implant (Go/C):A lightweight, cross-platform agent that executes on the target. It operates on a strict "pull" basis—polling the server for work to bypass inbound firewall restrictions. It is designed to be expendable.
    
    #Malleable Transport:Traffic camouflage. Communication profiles allow operators to customize headers, URIs, and user-agents to blend in with the environment (e.g., mimicking a jQuery update or a Windows background service).
    
    ## **Key Capabilities** 
    
    1. Asynchronous "Heartbeat" BeaconingSilence is survival. Unlike standard shells that maintain a noisy TCP connection, this implant sleeps for 95% of its lifecycle. It wakes, checks the queue, and vanishes again.
    
    2. Traffic Evasion (Jitter)Predictability gets you caught. To defeat Autocorrelation Analysis (detection based on precise timing patterns), the implant introduces chaos into its sleep cycle:$$ T_{sleep} = I \pm (I \times J) $$Where $I$ is the base interval and $J$ is the jitter coefficient (0.0 - 1.0).
    
    3. Cryptographic IntegrityWe assume the network is monitored.Transport: Enforced TLS 1.3 for network secrecy.Payload: Application-layer encryption using AES-256 (CBC). Even if SSL inspection is active, the tasking data remains a black box to the defender.
    
    ## **Usage & Verification**
    
    The architecture is useless without execution. For a complete walkthrough of the attack chain—from infrastructure provisioning to shell execution—refer to the Operational Usage Guide.Quick Start:
    
    ```bash
    
    # 1. Initialize the Team Server (The Brain)
python server/c2_controller.py --port 8080

    # 2. Compile the Agent (The Ghost)
cd implant/ && go build -ldflags "-w -s" -o beacon_linux main.go

    # 3. Queue a Command (The Mission)
python client/console.py <AGENT_ID> "whoami"


**View the Proof of Concept Gallery to see the kill-chain in action.

## **Detection Engineering**

To defeat the adversary, you must understand their tradecraft.A competent defender can hunt this framework by observing:

#Beaconing Frequency: While Jitter helps, long-duration connections to the same endpoint eventually generate a discernible pattern.

#Size Consistency: C2 heartbeats (without tasks) often have identical packet sizes (byte congruency).

#Process Anomalies: The beacon_linux binary spawning sh or cmd.exe is a high-confidence Indicator of Compromise (IoC).

### **Disclaimer**

**Authorized Testing Only.This software is a Proof of Concept developed for educational and defensive research purposes. It is designed to help security professionals understand adversary communication channels. The author (mauvehack) is not responsible for illegal use.

*Rules of Engagement: Use only on systems you own or have explicit permission to test.