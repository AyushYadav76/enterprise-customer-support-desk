
from config import CONFIDENCE_THRESHOLD
from shared_state import TicketState

from tools.escalation_tools import (
    check_escalation_required,
    create_human_review_record,
    submit_human_decision
)


class EscalationRouter:

    def __init__(self):
        self.name = "Escalation Router"
        self.human_review_queue = []

    def run(self, ticket: TicketState) -> TicketState:

        # Tool 1: Check whether escalation is required
        result = check_escalation_required(
            ticket.confidence,
            ticket.status,
            CONFIDENCE_THRESHOLD
        )

        if not result["required"]:

            ticket.add_trace(
                self.name,
                "completed",
                "No human escalation required."
            )

            return ticket

        reason = "; ".join(result["reasons"])

        if ticket.escalation_reason:
            reason += "; " + ticket.escalation_reason

        # Tool 2: Create human review record
        record = create_human_review_record(
            ticket.ticket_id,
            ticket.customer_id,
            ticket.message,
            reason
        )

        self.human_review_queue.append(record)

        ticket.update_status("escalated")
        ticket.human_review_status = "pending"
        ticket.escalation_reason = reason

        ticket.add_trace(
            self.name,
            "escalated",
            reason
        )

        return ticket

    def review_ticket(
        self,
        ticket: TicketState,
        decision: str,
        notes: str
    ) -> TicketState:

        # Tool 3: Submit human decision
        result = submit_human_decision(
            decision,
            notes
        )

        if not result["valid"]:
            raise ValueError(result["reason"])

        ticket.human_review_status = "completed"
        ticket.human_review_decision = result["decision"]
        ticket.human_review_notes = result["notes"]

        ticket.update_status(result["decision"])

        for record in self.human_review_queue:
            if record["ticket_id"] == ticket.ticket_id:
                record["queue_status"] = "completed"

        ticket.add_trace(
            self.name,
            "human_review_completed",
            f"Human decision: {decision}. Notes: {notes}"
        )

        return ticket


if __name__ == "__main__":

    ticket = TicketState(
        customer_id="CUST002",
        message="My account is locked.",
        category="account",
        confidence=0.9,
        status="needs_escalation"
    )

    router = EscalationRouter()

    ticket = router.run(ticket)

    print("\n===== ESCALATION RESULT =====")
    print("Status:", ticket.status)
    print("Reason:", ticket.escalation_reason)
    print("Queue:", router.human_review_queue)

    ticket = router.review_ticket(
        ticket,
        "resolved",
        "Customer identity verified and account unlocked."
    )

    print("\n===== HUMAN REVIEW RESULT =====")
    print("Status:", ticket.status)
    print("Decision:", ticket.human_review_decision)
