
from shared_state import TicketState

from tools.billing_tools import (
    search_billing_policy,
    check_transaction,
    evaluate_duplicate_payment
)


class BillingSpecialistAgent:

    def __init__(self):
        self.name = "Billing Specialist"

        self.transaction_store = {
            "TXN1001": {
                "amount": 1500,
                "status": "duplicate_verified",
                "currency": "INR"
            },

            "TXN1002": {
                "amount": 999,
                "status": "successful",
                "currency": "INR"
            }
        }

    def run(
        self,
        ticket: TicketState,
        transaction_id: str = None
    ) -> TicketState:

        if ticket.category != "billing":
            ticket.add_trace(
                self.name,
                "skipped",
                "Ticket is not classified as billing."
            )
            return ticket

        # Tool 1: Retrieve relevant billing policy
        policy = search_billing_policy(ticket.message)

        if not policy["found"]:
            ticket.update_status("needs_escalation")
            ticket.escalation_reason = (
                "Relevant billing policy could not be found."
            )

            ticket.add_trace(
                self.name,
                "failed",
                ticket.escalation_reason
            )

            return ticket

        # Tool 2: Check transaction
        if not transaction_id:
            ticket.update_status("needs_escalation")
            ticket.escalation_reason = (
                "Transaction ID is required for verification."
            )

            ticket.add_trace(
                self.name,
                "escalated",
                ticket.escalation_reason
            )

            return ticket

        result = check_transaction(
            transaction_id,
            self.transaction_store
        )

        if not result["found"]:
            ticket.update_status("needs_escalation")
            ticket.escalation_reason = result["reason"]

            ticket.add_trace(
                self.name,
                "escalated",
                ticket.escalation_reason
            )

            return ticket

        transaction = result["transaction"]

        # Tool 3: Evaluate duplicate payment
        evaluation = evaluate_duplicate_payment(transaction)

        if evaluation["eligible"]:

            ticket.resolution = (
                f"Verified duplicate payment of "
                f"{transaction['currency']} "
                f"{transaction['amount']}. "
                f"Eligible for refund review."
            )

            ticket.retrieved_sources.extend(
                policy["policies"]
            )

            ticket.update_status("resolved")

        else:

            ticket.resolution = evaluation["reason"]
            ticket.update_status("needs_escalation")

        ticket.add_trace(
            self.name,
            "completed",
            ticket.resolution
        )

        return ticket


if __name__ == "__main__":

    ticket = TicketState(
        customer_id="CUST001",
        message="I was charged twice for my subscription."
    )

    from agents.classifier_agent import ClassifierAgent

    ticket = ClassifierAgent().run(ticket)

    agent = BillingSpecialistAgent()

    ticket = agent.run(
        ticket,
        transaction_id="TXN1001"
    )

    print("\n===== BILLING SPECIALIST RESULT =====")
    print("Category:", ticket.category)
    print("Status:", ticket.status)
    print("Resolution:", ticket.resolution)
    print("Retrieved Policies:", len(ticket.retrieved_sources))

    print("\nAgent Trace:")

    for trace in ticket.agent_trace:
        print(trace.model_dump())
