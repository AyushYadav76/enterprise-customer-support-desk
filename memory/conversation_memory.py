
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


class ConversationMemory:
    """Persistent customer conversation memory using SQLite."""

    def __init__(self, db_path=None):
        if db_path is None:
            project_root = Path(__file__).resolve().parent.parent
            db_path = project_root / "memory" / "conversation_memory.db"

        self.db_path = str(db_path)
        self.initialize_database()

    def initialize_database(self):
        """Create the conversation table if it does not exist."""

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    ticket_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    category TEXT,
                    status TEXT,
                    resolution TEXT,
                    drafted_reply TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_customer_id
                ON conversations(customer_id)
            """)

    def save_ticket(self, ticket):
        """Save a completed ticket without overwriting existing records."""

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                INSERT OR IGNORE INTO conversations (
                    ticket_id,
                    customer_id,
                    message,
                    category,
                    status,
                    resolution,
                    drafted_reply,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.ticket_id,
                ticket.customer_id,
                ticket.message,
                ticket.category,
                ticket.status,
                ticket.resolution,
                ticket.drafted_reply,
                datetime.now(timezone.utc).isoformat()
            ))

    def get_recent_history(self, customer_id, limit=5):
        """Retrieve the most recent tickets for a customer."""

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute("""
                SELECT *
                FROM conversations
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (customer_id, limit)).fetchall()

        return [dict(row) for row in reversed(rows)]

    def format_history(self, customer_id, limit=5):
        """Convert previous tickets into readable context."""

        history = self.get_recent_history(customer_id, limit)

        if not history:
            return "No previous customer conversations found."

        formatted = []

        for index, ticket in enumerate(history, start=1):
            formatted.append(
                f"Previous Ticket {index}:\n"
                f"Message: {ticket['message']}\n"
                f"Category: {ticket['category']}\n"
                f"Status: {ticket['status']}\n"
                f"Resolution: {ticket['resolution'] or 'Not available'}"
            )

        return "\n\n".join(formatted)
