
from tools.classifier_tools import (
    validate_ticket,
    classify_ticket_by_rules
)

from shared_state import TicketState
from config import CONFIDENCE_THRESHOLD


class ClassifierAgent:

    def __init__(self):
        self.name = "Classifier Agent"

    def run(self, ticket: TicketState) -> TicketState:

        # Tool 1: Validate incoming ticket
        validation = validate_ticket(
            ticket.message,
            ticket.customer_id
        )

        if not validation["valid"]:

            ticket.update_status("invalid")

            ticket.add_trace(
                self.name,
                "failed",
                validation["reason"]
            )

            return ticket

        # Tool 2: Classify the ticket
        result = classify_ticket_by_rules(
            ticket.message
        )

        ticket.category = result["category"]
        ticket.confidence = result["confidence"]

        specialist_mapping = {
            "billing": "Billing Specialist",
            "technical": "Technical Specialist",
            "account": "Account Specialist",
            "other": None
        }

        ticket.assigned_specialist = specialist_mapping[
            ticket.category
        ]

        # Low-confidence tickets require escalation
        if ticket.confidence < CONFIDENCE_THRESHOLD:

            ticket.update_status("needs_escalation")

        else:

            ticket.update_status("classified")

        output = (
            f"Category: {ticket.category}; "
            f"Confidence: {ticket.confidence}; "
            f"Reason: {result['reason']}"
        )

        ticket.add_trace(
            self.name,
            "completed",
            output
        )

        return ticket


if __name__ == "__main__":

    ticket = TicketState(
        customer_id="CUST001",
        message="I was charged twice for my subscription."
    )

    agent = ClassifierAgent()

    result = agent.run(ticket)

    print("\n===== CLASSIFIER AGENT RESULT =====")

    print("Ticket ID:", result.ticket_id)
    print("Category:", result.category)
    print("Confidence:", result.confidence)
    print("Specialist:", result.assigned_specialist)
    print("Status:", result.status)

    print("\nAgent Trace:")

    for trace in result.agent_trace:
        print(trace.model_dump())
