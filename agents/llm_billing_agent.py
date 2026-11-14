
import asyncio
import ast
import json

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion

from plugins.billing_plugin import BillingPlugin


MODEL_NAME = "support-desk-ai"
OLLAMA_HOST = "http://localhost:11434"
SERVICE_ID = "local-ollama"


def parse_tool_result(result):
    """Safely convert plugin results into Python dictionaries."""

    raw = getattr(result, "value", result)

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return ast.literal_eval(raw)

    raise TypeError(f"Unexpected result type: {type(raw).__name__}")


class LLMBillingAgent:

    def __init__(self):

        self.kernel = Kernel()

        self.kernel.add_service(
            OllamaChatCompletion(
                service_id=SERVICE_ID,
                ai_model_id=MODEL_NAME,
                host=OLLAMA_HOST,
            )
        )

        self.kernel.add_plugin(
            BillingPlugin(),
            plugin_name="Billing",
        )

        self.agent_kernel = Kernel()

        self.agent_kernel.add_service(
            OllamaChatCompletion(
                service_id=SERVICE_ID,
                ai_model_id=MODEL_NAME,
                host=OLLAMA_HOST,
            )
        )


        self.agent = ChatCompletionAgent(
            kernel=self.agent_kernel,
            name="LLMBillingSpecialist",
            description="Investigates customer billing and payment issues.",
            instructions="""
            You are an enterprise billing specialist.

            Your responsibilities:
            - Explain verified billing investigation results.
            - Identify whether a duplicate payment was verified.
            - Explain refund eligibility according to retrieved policy.
            - Draft a professional customer-facing response.

            IMPORTANT:
            - Use only the supplied tool results.
            - Never invent transaction information.
            - Never claim a refund has been processed.
            - Eligibility for refund review is not a completed refund.
            - If transaction verification fails, recommend human review.
            - Always respond in English.


            IMPORTANT REFUND ACCURACY RULES:

            - Refund eligibility is not the same as refund approval.
            - Never claim that a refund has been initiated or processed.
            - Never claim that a refund review is underway unless a tool confirms it.
            - If a duplicate payment is verified and eligible, state:
            "The duplicate payment has been verified and is eligible
            for refund review."
            - Explain that further review or approval may be required.
            - Never invent actions performed by the support team.

            STRICT REFUND ACCURACY RULES:
            - Never say that a refund review is currently in progress unless a tool explicitly confirms it.
            - Never say that a refund has been initiated, approved, or processed unless a tool explicitly confirms it.
            - If evaluate_duplicate_payment returns eligible=True, state only:
            "The duplicate payment has been verified and is eligible for refund review."
            - Explain that eligibility does not mean approval or processing.
            - Do not invent a review timeline.
            - Do not promise when the customer will receive a refund.

            """,
        )

    async def investigate(
        self,
        customer_message: str,
        transaction_id: str,
        conversation_history: list[str] = None
    ) -> str:

        conversation_history = conversation_history or []

        # TOOL 1: Retrieve billing policy.
        policy_result = await self.kernel.invoke(
            plugin_name="Billing",
            function_name="search_billing_policy",
            query=customer_message,
        )

        policy = parse_tool_result(policy_result)

        print("\n[TOOL EXECUTED] search_billing_policy")
        print(policy)

        # TOOL 2: Look up transaction.
        transaction_result = await self.kernel.invoke(
            plugin_name="Billing",
            function_name="check_transaction",
            transaction_id=transaction_id,
        )

        transaction_data = parse_tool_result(transaction_result)

        print("\n[TOOL EXECUTED] check_transaction")
        print(transaction_data)

        evaluation = {
            "eligible": False,
            "reason": "Transaction could not be verified."
        }

        # TOOL 3: Evaluate a verified transaction.
        if transaction_data.get("found"):

            transaction = transaction_data["transaction"]

            evaluation_result = await self.kernel.invoke(
                plugin_name="Billing",
                function_name="evaluate_duplicate_payment",
                transaction_json=json.dumps(transaction),
            )

            evaluation = parse_tool_result(evaluation_result)

            print("\n[TOOL EXECUTED] evaluate_duplicate_payment")
            print(evaluation)

        verified_results = {
            "policy": policy,
            "transaction": transaction_data,
            "duplicate_payment_evaluation": evaluation,
        }

        
        prompt = f"""
        You are investigating a customer billing support ticket.

        PREVIOUS CUSTOMER CONVERSATIONS:
        {json.dumps(conversation_history, indent=2)}

        CURRENT CUSTOMER MESSAGE:
        {customer_message}

        TRANSACTION ID:
        {transaction_id}

        VERIFIED RESULTS FROM BILLING TOOLS:
        {json.dumps(verified_results, indent=2)}

        Instructions:

        1. Use previous conversations as context.
        2. Prioritize verified transaction and policy information.
        3. Do not ask for information already provided in previous conversations.
        4. If a previous billing issue remains unresolved, acknowledge it.
        5. Never invent transaction information.
        6. Never claim a refund has been processed or initiated.
        7. Refund eligibility is not refund approval.
        8. If a duplicate payment is verified and eligible, state:
        "The duplicate payment has been verified and is eligible
        for refund review."
        9. Explain that further review or approval may be required.
        10. If transaction verification fails, recommend human review.

        Prepare a professional billing investigation report containing:

        1. Investigation summary.
        2. Relevant previous conversation context.
        3. Transaction verification result.
        4. Refund eligibility.
        5. Customer-facing response.

        Always communicate in English.
        """


        response_parts = []

        async for response in self.agent.invoke(messages=prompt):

            content = getattr(response, "content", None)

            if isinstance(content, str):
                response_parts.append(content)

            elif content is not None:
                for item in getattr(content, "items", []):
                    text = getattr(item, "text", None)

                    if text:
                        response_parts.append(text)

                if not response_parts:
                    inner = getattr(content, "inner_content", None)
                    message = getattr(inner, "message", None)
                    raw_text = getattr(message, "content", None)

                    if raw_text:
                        response_parts.append(raw_text)

        final_response = "\n".join(response_parts).strip()

        if not final_response:
            raise RuntimeError("Billing Specialist generated an empty response.")

        # Build the customer-facing response using verified tool results.
        if not transaction_data.get("found"):
            customer_reply = (
                f"We could not verify transaction {transaction_id}. "
                "Our support team will need to review the transaction "
                "before we can determine refund eligibility."
            )

        elif evaluation.get("eligible") is True:
            customer_reply = (
                "The duplicate payment has been verified and is eligible "
                "for refund review. Please note that eligibility does not "
                "mean the refund has been approved or processed. "
                "Further review or approval may be required."
            )

        else:
            customer_reply = (
                "We checked the transaction, but it has not been confirmed "
                "as eligible for duplicate-payment refund review. "
                "Further investigation may be required."
            )

        return (
            f"{final_response}\n\n"
            "===== VERIFIED CUSTOMER-FACING RESPONSE =====\n"
            f"{customer_reply}"
        )


async def main():

    agent = LLMBillingAgent()

    customer_message = (
        "I was charged twice for my subscription. "
        "Please investigate the duplicate payment."
    )

    print("\n===== LLM BILLING SPECIALIST =====")

    result = await agent.investigate(
        customer_message=customer_message,
        transaction_id="TXN1001",
        conversation_history=[]
    )

    print("\n===== BILLING INVESTIGATION RESULT =====")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
