import asyncio
from orchestration.llm_support_manager import LLMSupportManager


async def test_account(customer_id, message):
    manager = LLMSupportManager()

    ticket = await manager.process_ticket(
        customer_id=customer_id,
        message=message
    )

    print("\n" + "=" * 55)
    print("CUSTOMER:", customer_id)
    print("CATEGORY:", ticket.category)
    print("SPECIALIST:", ticket.assigned_specialist)
    print("STATUS:", ticket.status)
    print("ESCALATION REASON:", ticket.escalation_reason)
    print("CUSTOMER REPLY:", ticket.drafted_reply)

    print("\nEXECUTION TRACE:")
    for item in ticket.agent_trace:
        print(item)


async def main():
    await test_account(
        "CUST001",
        "I cannot access my account. Please check my account."
    )

    await test_account(
        "CUST002",
        "My account is locked. Please help me regain access."
    )

    await test_account(
        "CUST003",
        "I cannot access my account. Please help me verify it."
    )


if __name__ == "__main__":
    asyncio.run(main())