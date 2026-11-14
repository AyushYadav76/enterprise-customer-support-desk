
from datetime import datetime, timezone


def check_escalation_required(
    confidence: float,
    status: str,
    threshold: float
) -> dict:
    """Determine whether a ticket needs human review."""

    reasons = []

    if confidence < threshold:
        reasons.append("Low classification confidence")

    if status in ["needs_escalation", "invalid"]:
        reasons.append("Specialist could not resolve the ticket")

    return {
        "required": len(reasons) > 0,
        "reasons": reasons
    }


def create_human_review_record(
    ticket_id: str,
    customer_id: str,
    message: str,
    reason: str
) -> dict:
    """Create a human review queue record."""

    return {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "message": message,
        "reason": reason,
        "queue_status": "pending",
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }


def submit_human_decision(
    decision: str,
    notes: str
) -> dict:
    """Validate a human review decision."""

    allowed = ["resolved", "rejected", "follow_up"]

    if decision not in allowed:
        return {
            "valid": False,
            "reason": "Invalid human decision."
        }

    if not notes.strip():
        return {
            "valid": False,
            "reason": "Human review notes are required."
        }

    return {
        "valid": True,
        "decision": decision,
        "notes": notes,
        "reviewed_at": datetime.now(
            timezone.utc
        ).isoformat()
    }
