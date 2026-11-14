
from shared_state import TicketState

from tools.account_tools import (
    lookup_account,
    verify_account_access,
    generate_account_guidance
)


class AccountSpecialistAgent:

    def __init__(self):
        self.name = "Account Specialist"

    def run(self, ticket: TicketState) -> TicketState:

        if ticket.category != "account":

            ticket.add_trace(
                self.name,
                "skipped",
                "Ticket is not classified as an account issue."
            )

            return ticket

        # Tool 1: Look up customer account
        lookup = lookup_account(ticket.customer_id)

        if not lookup["found"]:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = lookup["reason"]

            ticket.add_trace(
                self.name,
                "escalated",
                lookup["reason"]
            )

            return ticket

        account = lookup["account"]

        # Tool 2: Verify account access
        verification = verify_account_access(account)

        # Tool 3: Generate account guidance
        guidance = generate_account_guidance(account)

        ticket.resolution = guidance

        if not verification["accessible"]:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = verification["reason"]

            ticket.add_trace(
                self.name,
                "escalated",
                verification["reason"]
            )

            return ticket

        ticket.update_status("resolved")

        ticket.add_trace(
            self.name,
            "completed",
            guidance
        )

        return ticket


if __name__ == "__main__":

    from agents.classifier_agent import ClassifierAgent

    ticket = TicketState(
        customer_id="CUST001",
        message="I cannot login to my account."
    )

    ticket = ClassifierAgent().run(ticket)

    agent = AccountSpecialistAgent()

    ticket = agent.run(ticket)

    print("\n===== ACCOUNT SPECIALIST RESULT =====")
    print("Category:", ticket.category)
    print("Status:", ticket.status)
    print("Resolution:", ticket.resolution)

    print("\nAgent Trace:")

    for trace in ticket.agent_trace:
        print(trace.model_dump())
