import asyncio
from agents.llm_billing_agent import LLMBillingAgent

async def main():
    agent = LLMBillingAgent()

    result = await agent.investigate(
        customer_message="I was charged twice for my order. Please check the duplicate payment.",
        transaction_id="TXN1001",
        conversation_history=[]
    )

    print("\n===== BILLING SPECIALIST RESPONSE =====")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())