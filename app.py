"""
Databricks Support Ticket App:
- Serves a Flask API for support ticket management
- Reads/writes to Lakebase (Databricks-managed Postgres) via lakebase.py
- Manages tickets and ticket messages

Run locally:
    python app.py
Deploy as a Databricks App using app.yaml.
"""

import logging
import os
from datetime import datetime

from databricks.sdk import WorkspaceClient
from flask import Flask, jsonify, render_template, request

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, rely on environment variables

import lakebase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticket-app")

app = Flask(__name__)
_w = WorkspaceClient()

TICKETS_TABLE = os.environ.get("TICKETS_TABLE", "tickets")
MESSAGES_TABLE = os.environ.get("MESSAGES_TABLE", "ticket_messages")


def ensure_tables():
    """Create the tickets and messages tables in Lakebase if they don't exist yet."""
    # Create tickets table
    lakebase.run_write(
        f"""
        CREATE TABLE IF NOT EXISTS {TICKETS_TABLE} (
            ticket_id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    
    # Create ticket_messages table
    lakebase.run_write(
        f"""
        CREATE TABLE IF NOT EXISTS {MESSAGES_TABLE} (
            message_id SERIAL PRIMARY KEY,
            ticket_id INTEGER NOT NULL REFERENCES {TICKETS_TABLE}(ticket_id) ON DELETE CASCADE,
            message_text TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    
    # Create index for faster lookups by ticket_id
    lakebase.run_write(
        f"CREATE INDEX IF NOT EXISTS idx_messages_ticket_id ON {MESSAGES_TABLE}(ticket_id)"
    )
    
    # Create index for faster lookups by status
    lakebase.run_write(
        f"CREATE INDEX IF NOT EXISTS idx_tickets_status ON {TICKETS_TABLE}(status)"
    )


def _current_user_email() -> str:
    """
    Resolve the current user's email for ticket/message attribution.

    Databricks Apps inject the logged-in user's identity via the
    X-Forwarded-Email header on every request. Fall back to the Databricks
    SDK's current_user API for local development where that header isn't set.
    """
    header_email = request.headers.get("X-Forwarded-Email")
    if header_email:
        return header_email
    return _w.current_user.me().user_name


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.errorhandler(Exception)
def handle_exception(err):
    """Ensure all unhandled errors return JSON (not an HTML error page),
    so the frontend's resp.json() call never chokes on HTML."""
    logger.exception("Unhandled exception while processing request")
    status_code = getattr(err, "code", 500)
    if not isinstance(status_code, int):
        status_code = 500
    return jsonify({"error": str(err)}), status_code


@app.route("/")
def index():
    """Simple UI for ticket management."""
    return render_template("index.html")


@app.route("/api")
def api_info():
    """API documentation endpoint."""
    return jsonify({
        "message": "Ticket Support API",
        "endpoints": {
            "health": "GET /healthz",
            "list_tickets": "GET /tickets?status=open&limit=100",
            "create_ticket": "POST /tickets",
            "get_ticket": "GET /tickets/{id}",
            "update_ticket": "PUT /tickets/{id}",
            "delete_ticket": "DELETE /tickets/{id}",
            "add_message": "POST /tickets/{id}/messages",
            "delete_message": "DELETE /tickets/{id}/messages/{message_id}"
        }
    })


@app.route("/tickets", methods=["GET"])
def list_tickets():
    """List all tickets, optionally filtered by status."""
    ensure_tables()
    
    status = request.args.get("status")
    limit = int(request.args.get("limit", 100))
    
    if status:
        query = f"""
            SELECT ticket_id, title, status, created_by, created_at, updated_at 
            FROM {TICKETS_TABLE} 
            WHERE status = %s
            ORDER BY updated_at DESC 
            LIMIT %s
        """
        rows = lakebase.run_query(query, (status, limit))
    else:
        query = f"""
            SELECT ticket_id, title, status, created_by, created_at, updated_at 
            FROM {TICKETS_TABLE} 
            ORDER BY updated_at DESC 
            LIMIT %s
        """
        rows = lakebase.run_query(query, (limit,))
    
    return jsonify(rows)


@app.route("/tickets", methods=["POST"])
def create_ticket():
    """
    Create a new support ticket.
    """
    ensure_tables()
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    title = request.json.get("title", "").strip()
    status = request.json.get("status", "open").strip().lower()
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    if status not in ["open", "in_progress", "resolved", "closed"]:
        status = "open"
    
    email = _current_user_email()
    
    rows = lakebase.run_query(
        f"""
        INSERT INTO {TICKETS_TABLE} (title, status, created_by)
        VALUES (%s, %s, %s)
        RETURNING ticket_id, title, status, created_by, created_at, updated_at
        """,
        (title, status, email),
    )
    
    return jsonify(rows[0] if rows else {}), 201


@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Get a specific ticket with all its messages."""
    ensure_tables()
    
    # Get ticket details
    ticket_rows = lakebase.run_query(
        f"""
        SELECT ticket_id, title, status, created_by, created_at, updated_at 
        FROM {TICKETS_TABLE} 
        WHERE ticket_id = %s
        """,
        (ticket_id,),
    )
    
    if not ticket_rows:
        return jsonify({"error": "Ticket not found"}), 404
    
    ticket = ticket_rows[0]
    
    # Get ticket messages
    message_rows = lakebase.run_query(
        f"""
        SELECT message_id, ticket_id, message_text, author, created_at 
        FROM {MESSAGES_TABLE} 
        WHERE ticket_id = %s
        ORDER BY created_at ASC
        """,
        (ticket_id,),
    )
    
    ticket["messages"] = message_rows
    return jsonify(ticket)


@app.route("/tickets/<int:ticket_id>", methods=["PUT"])
def update_ticket(ticket_id):
    """
    Update a ticket's status or title.
    """
    ensure_tables()
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    title = request.json.get("title")
    status = request.json.get("status")
    
    if not title and not status:
        return jsonify({"error": "Either title or status must be provided"}), 400
    
    if status and status not in ["open", "in_progress", "resolved", "closed"]:
        return jsonify({"error": "Invalid status"}), 400
    
    # Build dynamic update query
    updates = []
    params = []
    
    if title:
        updates.append("title = %s")
        params.append(title)
    
    if status:
        updates.append("status = %s")
        params.append(status)
    
    updates.append("updated_at = now()")
    params.append(ticket_id)
    
    query = f"""
        UPDATE {TICKETS_TABLE}
        SET {', '.join(updates)}
        WHERE ticket_id = %s
        RETURNING ticket_id, title, status, created_by, created_at, updated_at
    """
    
    rows = lakebase.run_query(query, tuple(params))
    
    if not rows:
        return jsonify({"error": "Ticket not found"}), 404
    
    return jsonify(rows[0])


@app.route("/tickets/<int:ticket_id>/messages", methods=["POST"])
def add_message(ticket_id):
    """
    Add a message to a ticket.
    """
    ensure_tables()
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    message_text = request.json.get("message_text", "").strip()
    
    if not message_text:
        return jsonify({"error": "Message text is required"}), 400
    
    # Check if ticket exists
    ticket_rows = lakebase.run_query(
        f"SELECT ticket_id FROM {TICKETS_TABLE} WHERE ticket_id = %s",
        (ticket_id,),
    )
    
    if not ticket_rows:
        return jsonify({"error": "Ticket not found"}), 404
    
    email = _current_user_email()
    
    rows = lakebase.run_query(
        f"""
        INSERT INTO {MESSAGES_TABLE} (ticket_id, message_text, author)
        VALUES (%s, %s, %s)
        RETURNING message_id, ticket_id, message_text, author, created_at
        """,
        (ticket_id, message_text, email),
    )
    
    # Update ticket's updated_at timestamp
    lakebase.run_write(
        f"UPDATE {TICKETS_TABLE} SET updated_at = now() WHERE ticket_id = %s",
        (ticket_id,),
    )
    
    return jsonify(rows[0] if rows else {}), 201


@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    """
    Delete a ticket and all its messages.
    """
    ensure_tables()
    
    # Check if ticket exists
    ticket_rows = lakebase.run_query(
        f"SELECT ticket_id FROM {TICKETS_TABLE} WHERE ticket_id = %s",
        (ticket_id,),
    )
    
    if not ticket_rows:
        return jsonify({"error": "Ticket not found"}), 404
    
    # Delete ticket (messages will cascade delete due to foreign key)
    lakebase.run_write(
        f"DELETE FROM {TICKETS_TABLE} WHERE ticket_id = %s",
        (ticket_id,),
    )
    
    return jsonify({"ticket_id": ticket_id, "deleted": True})


@app.route("/tickets/<int:ticket_id>/messages/<int:message_id>", methods=["DELETE"])
def delete_message(ticket_id, message_id):
    """
    Delete a specific message from a ticket.
    """
    ensure_tables()
    
    # Check if message exists and belongs to the ticket
    message_rows = lakebase.run_query(
        f"""
        SELECT message_id FROM {MESSAGES_TABLE} 
        WHERE message_id = %s AND ticket_id = %s
        """,
        (message_id, ticket_id),
    )
    
    if not message_rows:
        return jsonify({"error": "Message not found"}), 404
    
    lakebase.run_write(
        f"DELETE FROM {MESSAGES_TABLE} WHERE message_id = %s",
        (message_id,),
    )
    
    # Update ticket's updated_at timestamp
    lakebase.run_write(
        f"UPDATE {TICKETS_TABLE} SET updated_at = now() WHERE ticket_id = %s",
        (ticket_id,),
    )
    
    return jsonify({"message_id": message_id, "deleted": True})


if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 8000))
    app.run(debug=True, host=host, port=port)
    print(f"Flask app running on http://{host}:{port}")
