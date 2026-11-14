
import asyncio
import ast
import json

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.functions import KernelArguments

from plugins.account_plugin import AccountPlugin


MODEL_NAME = "support-desk-ai"
OLLAMA_HOST = "http://localhost:11434"
SERVICE_ID = "local-ollama"


def parse_tool_result(result):
    """Convert Semantic Kernel tool results into Python objects."""

    raw = getattr(result, "value", result)

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return ast.literal_eval(raw)

    raise TypeError(
        f"Unexpected result type: {type(raw).__name__}"
    )


class LLMAccountAgent:

    def __init__(self):

       
        # Kernel 1: Explicit Python tool execution
        self.kernel = Kernel()
        self.last_investigation = {}

        self.kernel.add_service(
            OllamaChatCompletion(
                service_id=SERVICE_ID,
                ai_model_id=MODEL_NAME,
                host=OLLAMA_HOST,
            )
        )

        self.kernel.add_plugin(
            AccountPlugin(),
            plugin_name="Account",
        )

        # Kernel 2: LLM report generation only
        self.llm_kernel = Kernel()

        self.llm_kernel.add_service(
            OllamaChatCompletion(
                service_id=SERVICE_ID,
                ai_model_id=MODEL_NAME,
                host=OLLAMA_HOST,
            )
        )

        self.agent = ChatCompletionAgent(
            kernel=self.llm_kernel,
            name="LLMAccountSpecialist",
            description="Investigates customer account and access problems.",
            instructions="""
            You are an enterprise account support specialist.

            You receive verified account information from Python tools.
            Your job is to explain those results accurately.

            STRICT FACTUAL RULES:
            1. Never invent customer history or previous complaints.
            2. Never describe an account as locked unless locked=True.
            3. Never describe email as verified unless email_verified=True.
            4. An active account can still be inaccessible.
            5. An unverified email does NOT mean the account is locked.
            6. Follow the exact access verification result.
            7. Never claim that an account was unlocked or modified.
            8. Never invent actions performed by the support team.
            9. Do not contradict any supplied tool result.
            10. If uncertain, repeat the verified tool result rather
                than making an assumption.

            Use the following fields exactly:
            - status
            - email_verified
            - locked
            - accessible
            - reason
            - guidance

            Prepare:
            1. Issue summary.
            2. Account lookup result.
            3. Access verification result.
            4. Recommended guidance.
            5. Customer-facing response.

            Use professional, concise English.
            Never request passwords or authentication secrets.
            """,
        )


    async def investigate(
        self,
        customer_message: str,
        customer_id: str,
        conversation_history: list[str] = None
    ) -> str:
        conversation_history = conversation_history or []

        # TOOL 1: Look up customer account.
        lookup_result = await self.kernel.invoke(
            plugin_name="Account",
            function_name="lookup_account",
            arguments=KernelArguments(
                customer_id=customer_id
            ),
        )

        account_data = parse_tool_result(lookup_result)

        print("\n[TOOL EXECUTED] lookup_account")
        print(account_data)

        access_result = {
            "accessible": False,
            "reason": "Account could not be verified."
        }

        guidance = "Human review is recommended."

        if account_data.get("found"):

            # Extract the actual account dictionary.
            account = account_data["account"]

            # TOOL 2: Verify account access.
            verification_result = await self.kernel.invoke(
                plugin_name="Account",
                function_name="verify_account_access",
                arguments=KernelArguments(
                    account_json=json.dumps(account)
                ),
            )

            access_result = parse_tool_result(
                verification_result
            )

            print("\n[TOOL EXECUTED] verify_account_access")
            print(access_result)

            # TOOL 3: Generate account guidance.
            guidance_result = await self.kernel.invoke(
                plugin_name="Account",
                function_name="generate_account_guidance",
                arguments=KernelArguments(
                    account_json=json.dumps(account)
                ),
            )

            guidance_data = parse_tool_result(
                guidance_result
            )

            guidance = guidance_data.get(
                "guidance",
                "Human review is recommended."
            )

            print("\n[TOOL EXECUTED] generate_account_guidance")
            print(guidance)

        verified_results = {
            "account_lookup": account_data,
            "access_verification": access_result,
            "account_guidance": guidance,
        }
        
        self.last_investigation = verified_results

        prompt = f"""
        You are investigating a customer account support ticket.

        PREVIOUS CUSTOMER CONVERSATIONS:
        {json.dumps(conversation_history, indent=2)}

        CURRENT CUSTOMER MESSAGE:
        {customer_message}

        CUSTOMER ID:
        {customer_id}

        VERIFIED RESULTS FROM ACCOUNT TOOLS:
        {json.dumps(verified_results, indent=2)}

        INSTRUCTIONS:

        1. Use previous conversations as context.
        2. Prioritize the current customer message and verified account-tool results.
        3. Do not ask for information already provided in previous conversations.
        4. If the customer previously reported an unresolved account issue, acknowledge it.
        5. Never invent account information.
        6. Do not assume an account is unlocked or verified.
        7. Do not claim that an account has been unlocked unless a tool explicitly confirms it.
        8. If account lookup fails or access is unavailable, recommend human review.
        9. Always communicate in English.

        PREPARE AN ACCOUNT SUPPORT INVESTIGATION REPORT:

        1. Issue summary.
        2. Relevant previous conversation context.
        3. Account lookup result.
        4. Access verification result.
        5. Recommended guidance.
        6. Customer-facing response.
        """

        response_parts = []

        async for response in self.agent.invoke(messages=prompt):
            if response.content:
                response_parts.append(str(response.content))

        return "\n".join(response_parts)


async def main():

    agent = LLMAccountAgent()

    customer_message = (
        "I cannot access my account. "
        "Please check my account status."
    )

    print("\n===== LLM ACCOUNT SPECIALIST =====")
    print("\nCustomer:", customer_message)

    result = await agent.investigate(
        customer_message=customer_message,
        customer_id="CUST003",
    )

    print("\n===== ACCOUNT INVESTIGATION RESULT =====")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
