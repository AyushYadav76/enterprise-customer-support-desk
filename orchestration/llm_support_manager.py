
import asyncio
import json
import os

from datetime import datetime, timezone

from config import CONFIDENCE_THRESHOLD, LOG_DIRECTORY
from shared_state import TicketState

from agents.llm_classifier_agent import LLMClassifierAgent
from agents.llm_billing_agent import LLMBillingAgent
from agents.llm_technical_agent import LLMTechnicalAgent
from agents.llm_account_agent import LLMAccountAgent

from agents.escalation_router import EscalationRouter

from memory.conversation_memory import ConversationMemory

class LLMSupportManager:
    """
    Central orchestration manager for the LLM-powered
    customer support triage and resolution system.
    """

    def __init__(self):

        self.classifier = LLMClassifierAgent()

        self.billing_agent = LLMBillingAgent()

        self.technical_agent = LLMTechnicalAgent()

        self.account_agent = LLMAccountAgent()

        self.escalation_router = EscalationRouter()

        self.memory = ConversationMemory()

        os.makedirs(LOG_DIRECTORY, exist_ok=True)

        self.run_log_path = os.path.join(
            LOG_DIRECTORY,
            "llm_agent_runs.jsonl"
        )

    def write_run_log(self, ticket: TicketState):
        """
        Append the completed ticket execution to a JSONL log.
        Existing log records are never overwritten.
        """

        record = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "ticket": ticket.model_dump(mode="json")
        }

        with open(
            self.run_log_path,
            "a",
            encoding="utf-8"
        ) as log_file:

            log_file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )

    async def process_ticket(
        self,
        customer_id: str,
        message: str,
        transaction_id: str = None
    ) -> TicketState:

        # STEP 1: Create shared ticket state.
        ticket = TicketState(
            customer_id=customer_id,
            message=message
        )

        # Retrieve previous conversations for this customer.
        previous_history = self.memory.get_recent_history(
            customer_id,
            limit=5
        )

        ticket.conversation_history = [
            f"Previous message: {item['message']} | "
            f"Category: {item['category']} | "
            f"Status: {item['status']} | "
            f"Resolution: {item['resolution'] or 'Not available'}"
            for item in previous_history
        ]

        ticket.add_trace(
            "Conversation Memory",
            "completed",
            f"Retrieved {len(previous_history)} previous conversation(s)."
        )

        ticket.add_trace(
            "LLM Support Manager",
            "started",
            "New customer support ticket received."
        )

        try:

            # STEP 2: Classify and validate the ticket.
            classification = await self.classifier.classify(
                message=message,
                customer_id=customer_id
            )

            if not classification.get("valid"):

                ticket.category = "other"
                ticket.confidence = 0.0

                ticket.update_status("invalid")

                ticket.escalation_reason = classification.get(
                    "reason",
                    "Ticket validation failed."
                )

                ticket.add_trace(
                    "LLM Classifier Agent",
                    "invalid",
                    ticket.escalation_reason
                )

                ticket = self.escalation_router.run(ticket)

                self.memory.save_ticket(ticket)
                self.write_run_log(ticket)

                return ticket

            # Store verified classification results.
            ticket.category = classification["category"]

            ticket.confidence = float(
                classification["confidence"]
            )

            ticket.add_trace(
                "LLM Classifier Agent",
                "completed",
                json.dumps({
                    "category": ticket.category,
                    "confidence": ticket.confidence,
                    "reason": classification["reason"],
                    "explanation": classification["explanation"]
                })
            )

            # STEP 3: Check classification confidence.
            if ticket.confidence < CONFIDENCE_THRESHOLD:

                ticket.update_status("needs_escalation")

                ticket.escalation_reason = (
                    f"Classification confidence "
                    f"{ticket.confidence} is below "
                    f"the required threshold "
                    f"{CONFIDENCE_THRESHOLD}."
                )

                ticket = self.escalation_router.run(ticket)

                self.memory.save_ticket(ticket)
                self.write_run_log(ticket)

                return ticket

            # STEP 4: Route to the correct specialist.
            if ticket.category == "billing":

                ticket.assigned_specialist = "Billing Specialist"

                # A transaction ID is necessary for transaction
                # verification in the current Billing Agent.
                if not transaction_id:

                    ticket.update_status("needs_escalation")

                    ticket.escalation_reason = (
                        "Transaction ID is required for "
                        "billing investigation."
                    )

                    ticket.add_trace(
                        "LLM Support Manager",
                        "waiting_for_information",
                        ticket.escalation_reason
                    )

                    ticket = self.escalation_router.run(ticket)

                    self.memory.save_ticket(ticket)
                    self.write_run_log(ticket)

                    return ticket

                specialist_result = (
                    await self.billing_agent.investigate(
                        customer_message=message,
                        transaction_id=transaction_id,
                        conversation_history=ticket.conversation_history
                    )
                )

            elif ticket.category == "technical":

                ticket.assigned_specialist = "Technical Specialist"

                specialist_result = (
                    await self.technical_agent.investigate(
                        customer_message=message,
                        conversation_history=ticket.conversation_history
                    )
                )

            elif ticket.category == "account":

                ticket.assigned_specialist = "Account Specialist"

                specialist_result = (
                    await self.account_agent.investigate(
                        customer_message=message,
                        customer_id=customer_id,
                        conversation_history=ticket.conversation_history
                    )
                )

            else:

                ticket.update_status("needs_escalation")

                ticket.escalation_reason = (
                    "No suitable specialist found for "
                    f"category: {ticket.category}"
                )

                ticket = self.escalation_router.run(ticket)

                self.memory.save_ticket(ticket)
                self.write_run_log(ticket)

                return ticket

            # STEP 5: Store specialist results.
            ticket.resolution = (
                "Specialist investigation completed. "
                "A customer-facing response was generated."
            )

            # BILLING: Store only the verified customer-facing response.
            if ticket.category == "billing":
                marker = "===== VERIFIED CUSTOMER-FACING RESPONSE ====="

                if marker not in specialist_result:
                    raise ValueError(
                        "Billing Specialist did not generate a verified customer response."
                    )

                ticket.drafted_reply = specialist_result.split(marker, 1)[1].strip()
                ticket.update_status("response_drafted")

            # ACCOUNT: Store response and inspect verified tool results.
            elif ticket.category == "account":
                ticket.drafted_reply = specialist_result

                investigation = self.account_agent.last_investigation or {}

                account_lookup = investigation.get("account_lookup", {})
                access_verification = investigation.get("access_verification", {})

                if not account_lookup.get("found", False):
                    ticket.update_status("needs_escalation")
                    ticket.escalation_reason = (
                        "Customer account could not be found or verified. "
                        "Human account support is required."
                    )

                elif access_verification.get("accessible") is not True:
                    ticket.update_status("needs_escalation")
                    ticket.escalation_reason = (
                        "Account access verification failed. "
                        + access_verification.get(
                            "reason",
                            "Human account support is required."
                        )
                    )

                else:
                    ticket.update_status("response_drafted")

            # OTHER SPECIALISTS
            else:
                ticket.drafted_reply = specialist_result
                ticket.update_status("response_drafted")

            ticket.add_trace(
                ticket.assigned_specialist,
                "completed",
                specialist_result
            )

            # STEP 6: Check human escalation requirements.
            ticket = self.escalation_router.run(ticket)

            # STEP 7: Record final manager execution.
            ticket.add_trace(
                "LLM Support Manager",
                "completed",
                "Ticket processing workflow completed."
            )

        except Exception as error:

            # Record failures rather than silently losing tickets.
            ticket.update_status("needs_escalation")

            ticket.escalation_reason = (
                f"Agent execution failure: "
                f"{type(error).__name__}: {error}"
            )

            ticket.add_trace(
                "LLM Support Manager",
                "failed",
                ticket.escalation_reason
            )

            ticket = self.escalation_router.run(ticket)

        # STEP 8: Append final ticket to execution log.
        self.memory.save_ticket(ticket)
        self.write_run_log(ticket)

        return ticket


async def main():

    manager = LLMSupportManager()

    result = await manager.process_ticket(
        customer_id="CUST001",
        message=(
            "I was charged twice for my subscription. "
            "Please investigate the duplicate payment."
        ),
        transaction_id="TXN1001"
    )

    print("\n========== LLM SUPPORT DESK RESULT ==========")

    print("Ticket ID:", result.ticket_id)
    print("Customer:", result.customer_id)
    print("Category:", result.category)
    print("Confidence:", result.confidence)
    print("Specialist:", result.assigned_specialist)
    print("Status:", result.status)
    print("Resolution:", result.resolution)

    print("\n========== SPECIALIST RESPONSE ==========")
    print(result.drafted_reply)

    print("\n========== AGENT EXECUTION TRACE ==========")

    for trace in result.agent_trace:

        print(f"\nAgent: {trace.agent_name}")
        print(f"Status: {trace.status}")
        print(f"Output: {trace.output}")

    print("\nExecution log:", manager.run_log_path)

    print("\n============================================")


if __name__ == "__main__":
    asyncio.run(main())
