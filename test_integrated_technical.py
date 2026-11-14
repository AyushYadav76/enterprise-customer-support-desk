
import asyncio
from orchestration.llm_support_manager import LLMSupportManager


async def main():
    manager = LLMSupportManager()

    ticket = await manager.process_ticket(
        customer_id="CUST_TECH_RAG_TEST",
        message="My application keeps crashing even after restarting."
    )

    print("\n========== INTEGRATED TECHNICAL WORKFLOW ==========")
    print("Ticket ID:", ticket.ticket_id)
    print("Category:", ticket.category)
    print("Confidence:", ticket.confidence)
    print("Assigned Specialist:", ticket.assigned_specialist)
    print("Status:", ticket.status)

    print("\n========== RESOLUTION ==========")
    print(ticket.resolution)

    print("\n========== CUSTOMER REPLY ==========")
    print(ticket.drafted_reply)

    print("\n========== EXECUTION TRACE ==========")
    for item in ticket.agent_trace:
        print(item)


if __name__ == "__main__":
    asyncio.run(main())
