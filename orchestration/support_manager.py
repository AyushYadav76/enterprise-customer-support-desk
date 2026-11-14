
from shared_state import TicketState

from agents.classifier_agent import ClassifierAgent
from agents.billing_agent import BillingSpecialistAgent
from agents.technical_agent import TechnicalSpecialistAgent
from agents.account_agent import AccountSpecialistAgent
from agents.escalation_router import EscalationRouter


class SupportManager:

    def __init__(self):

        self.classifier = ClassifierAgent()

        self.billing_agent = BillingSpecialistAgent()

        self.technical_agent = TechnicalSpecialistAgent()

        self.account_agent = AccountSpecialistAgent()

        self.escalation_router = EscalationRouter()

    def process_ticket(
        self,
        customer_id: str,
        message: str,
        transaction_id: str = None
    ) -> TicketState:

        # Step 1: Create shared ticket state
        ticket = TicketState(
            customer_id=customer_id,
            message=message
        )

        # Step 2: Classify the ticket
        ticket = self.classifier.run(ticket)

        # Stop if ticket is invalid
        if ticket.status == "invalid":

            return self.escalation_router.run(ticket)

        # Stop if classification confidence is too low
        if ticket.status == "needs_escalation":

            return self.escalation_router.run(ticket)

        # Step 3: Route to the appropriate specialist
        if ticket.category == "billing":

            ticket = self.billing_agent.run(
                ticket,
                transaction_id
            )

        elif ticket.category == "technical":

            ticket = self.technical_agent.run(ticket)

        elif ticket.category == "account":

            ticket = self.account_agent.run(ticket)

        else:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = (
                "No suitable specialist found for this ticket."
            )

        # Step 4: Check escalation requirements
        ticket = self.escalation_router.run(ticket)

        # Step 5: Return complete ticket state
        return ticket


if __name__ == "__main__":

    manager = SupportManager()

    # Demonstration 1: Billing issue
    result = manager.process_ticket(
        customer_id="CUST001",
        message="I was charged twice for my subscription.",
        transaction_id="TXN1001"
    )

    print("\n========== SUPPORT DESK RESULT ==========")

    print("Ticket ID:", result.ticket_id)
    print("Customer:", result.customer_id)
    print("Category:", result.category)
    print("Confidence:", result.confidence)
    print("Specialist:", result.assigned_specialist)
    print("Status:", result.status)
    print("Resolution:", result.resolution)

    print("\n========== AGENT EXECUTION TRACE ==========")

    for trace in result.agent_trace:

        print(
            f"\nAgent: {trace.agent_name}"
            f"\nStatus: {trace.status}"
            f"\nOutput: {trace.output}"
        )

    print("\n==========================================")
