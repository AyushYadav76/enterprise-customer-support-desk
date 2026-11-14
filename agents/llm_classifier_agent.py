
import ast
import asyncio
import json

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.functions import KernelArguments

from plugins.classifier_plugin import ClassifierPlugin


MODEL_NAME = "support-desk-ai"
OLLAMA_HOST = "http://localhost:11434"
SERVICE_ID = "local-ollama"


def parse_tool_result(result):
    """Convert Semantic Kernel tool output into Python objects."""

    raw = getattr(result, "value", result)

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return ast.literal_eval(raw)

    raise TypeError(
        f"Unexpected tool result type: {type(raw).__name__}"
    )


class LLMClassifierAgent:

    def __init__(self):

        # Kernel for deterministic Python tool execution.
        self.kernel = Kernel()

        self.kernel.add_service(
            OllamaChatCompletion(
                service_id=SERVICE_ID,
                ai_model_id=MODEL_NAME,
                host=OLLAMA_HOST,
            )
        )

        self.kernel.add_plugin(
            ClassifierPlugin(),
            plugin_name="Classifier",
        )

        # Separate kernel for LLM explanation.
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
            name="LLMClassifierAgent",
            description="Classifies customer support tickets.",
            instructions="""
            You are an enterprise customer support classification agent.

            Explain the verified classification results supplied to you.

            Rules:
            - Preserve the exact category.
            - Preserve the exact confidence.
            - Preserve the classification reason.
            - Never invent or modify tool results.
            - Never perform classification using assumptions.
            - Always respond in English.
            """,
        )

    async def classify(
        self,
        message: str,
        customer_id: str
    ) -> dict:

        # TOOL 1: Validate ticket.
        validation_result = await self.kernel.invoke(
            plugin_name="Classifier",
            function_name="validate_support_ticket",
            arguments=KernelArguments(
                message=message,
                customer_id=customer_id,
            ),
        )

        validation_data = parse_tool_result(validation_result)

        print("\n[TOOL EXECUTED] validate_support_ticket")
        print(validation_data)

        if not validation_data.get("valid"):

            return {
                "valid": False,
                "category": "other",
                "confidence": 0.0,
                "reason": validation_data.get(
                    "reason",
                    "Ticket validation failed."
                ),
                "explanation": "The ticket requires correction.",
            }

        # TOOL 2: Classify ticket.
        classification_result = await self.kernel.invoke(
            plugin_name="Classifier",
            function_name="classify_support_ticket",
            arguments=KernelArguments(
                message=message
            ),
        )

        classification_data = parse_tool_result(
            classification_result
        )

        print("\n[TOOL EXECUTED] classify_support_ticket")
        print(classification_data)

        # Ask the LLM to explain verified results.
        prompt = f"""
        Customer message:
        {message}

        Customer ID:
        {customer_id}

        Verified classification:
        {json.dumps(classification_data, indent=2)}

        Explain the classification to the support desk.

        Preserve these exact values:
        Category: {classification_data["category"]}
        Confidence: {classification_data["confidence"]}
        Reason: {classification_data["reason"]}

        Do not modify these values.
        """

        response_parts = []

        async for response in self.agent.invoke(messages=prompt):

            if response.content:
                response_parts.append(str(response.content))

        explanation = "\n".join(response_parts)

        # Return structured information for central routing.
        return {
            "valid": True,
            "category": classification_data["category"],
            "confidence": classification_data["confidence"],
            "reason": classification_data["reason"],
            "explanation": explanation,
        }


async def main():

    agent = LLMClassifierAgent()

    message = (
        "I was charged twice for my subscription. "
        "Please investigate the duplicate payment."
    )

    result = await agent.classify(
        message=message,
        customer_id="CUST001",
    )

    print("\n===== STRUCTURED CLASSIFICATION =====")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
