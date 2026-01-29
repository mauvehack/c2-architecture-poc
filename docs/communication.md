# C2 Communication Protocol Specification

## Overview
Traffic between the Agent and Team Server simulates a standard HTTP web browsing session. 
All operational data is encapsulated within standard HTTP headers and body content, wrapped in JSON.

## Transport Layer
* **Protocol:** HTTP (Port 80) or HTTPS (Port 443)
* **Encryption:** TLS 1.3 (if HTTPS) + AES-256 Payload Encryption

## 1. Registration (Handshake)
**Direction:** Agent -> Server
**Method:** `POST`
**URI:** `/api/v1/register`
**Payload:**
```json
{
  "hostname": "WORKSTATION-01",
  "platform": "windows",
  "username": "admin"
}