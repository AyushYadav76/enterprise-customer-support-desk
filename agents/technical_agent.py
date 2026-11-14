
from shared_state import TicketState

from tools.technical_tools import (
    search_technical_knowledge,
    validate_technical_solution,
    check_error_severity
)


class TechnicalSpecialistAgent:

    def __init__(self):
        self.name = "Technical Specialist"

    def run(self, ticket: TicketState) -> TicketState:

        if ticket.category != "technical":

            ticket.add_trace(
                self.name,
                "skipped",
                "Ticket is not classified as technical."
            )

            return ticket

        # Tool 1: Check error severity
        severity = check_error_severity(ticket.message)

        if severity["requires_human"]:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = severity["reason"]

            ticket.add_trace(
                self.name,
                "escalated",
                severity["reason"]
            )

            return ticket

        # Tool 2: Retrieve technical knowledge
        knowledge = search_technical_knowledge(
            ticket.message
        )

        if not knowledge["found"]:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = (
                "No relevant technical documentation found."
            )

            ticket.add_trace(
                self.name,
                "escalated",
                ticket.escalation_reason
            )

            return ticket

        # Build a knowledge-grounded resolution
        resolution = "\n".join(
            item["content"]
            for item in knowledge["results"]
        )

        # Tool 3: Validate the solution
        validation = validate_technical_solution(
            resolution
        )

        if not validation["valid"]:

            ticket.update_status("needs_escalation")

            ticket.escalation_reason = validation["reason"]

            ticket.add_trace(
                self.name,
                "failed",
                validation["reason"]
            )

            return ticket

        ticket.resolution = (
            "Recommended troubleshooting steps:\n"
            + resolution
        )

        ticket.retrieved_sources.extend(
            item["content"]
            for item in knowledge["results"]
        )

        ticket.update_status("resolved")

        ticket.add_trace(
            self.name,
            "completed",
            "Technical solution retrieved and validated."
        )

        return ticket


if __name__ == "__main__":

    from agents.classifier_agent import ClassifierAgent

    ticket = TicketState(
        customer_id="CUST002",
        message="My application keeps crashing."
    )

    ticket = ClassifierAgent().run(ticket)

    agent = TechnicalSpecialistAgent()

    ticket = agent.run(ticket)

    print("\n===== TECHNICAL SPECIALIST RESULT =====")

    print("Category:", ticket.category)
    print("Status:", ticket.status)
    print("Resolution:", ticket.resolution)

    print("\nAgent Trace:")

    for trace in ticket.agent_trace:
        print(trace.model_dump())
