
import asyncio
import ast
import json

from click import prompt
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion

from plugins.technical_plugin import TechnicalPlugin


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

    raise TypeError(f"Unexpected result type: {type(raw).__name__}")


class LLMTechnicalAgent:

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
            TechnicalPlugin(),
            plugin_name="Technical",
        )

        self.agent = ChatCompletionAgent(
            kernel=self.kernel,
            name="LLMTechnicalSpecialist",
            description="Investigates and resolves technical support tickets.",
            instructions="""
            You are an enterprise technical support specialist.

            Your responsibilities:
            - Understand technical problems.
            - Explain retrieved technical knowledge.
            - Identify serious issues requiring human attention.
            - Recommend safe, relevant troubleshooting steps.
            - Produce a professional customer-facing response.

            IMPORTANT:
            - Use only the supplied tool results.
            - Never invent technical FAQ content.
            - Never claim that a technical issue is fixed without evidence.
            - If a tool indicates human review is required,
              recommend escalation.
            - Always communicate in English.
            """,
        )

    async def investigate(
        self,
        customer_message: str,
        conversation_history: list[str] = None
    ) -> str:

        conversation_history = conversation_history or []

        # TOOL 1: Check technical issue severity.
        severity_result = await self.kernel.invoke(
            plugin_name="Technical",
            function_name="check_error_severity",
            message=customer_message,
        )

        severity = parse_tool_result(severity_result)

        print("\n[TOOL EXECUTED] check_error_severity")
        print(severity)

        # TOOL 2: Retrieve relevant technical FAQ.
        knowledge_result = await self.kernel.invoke(
            plugin_name="Technical",
            function_name="search_technical_knowledge",
            query=customer_message,
        )

        knowledge = parse_tool_result(knowledge_result)

        print("\n[TOOL EXECUTED] search_technical_knowledge")
        print(knowledge)

        # Prepare a proposed solution using retrieved FAQ content.
        
        # Prepare retrieved articles and identify attempted steps.
        retrieved_articles = knowledge.get("results", [])

        previous_context = " ".join(conversation_history).lower()
        current_context = customer_message.lower()
        combined_context = previous_context + " " + current_context

        attempted_steps = []

        # Detect troubleshooting steps already attempted.
        if any(word in combined_context for word in [
            "restart", "restarted", "restarting"
        ]):
            attempted_steps.append("restart")

        if any(word in combined_context for word in [
            "updated", "update the application",
            "up to date", "latest version"
        ]):
            attempted_steps.append("update")

        if any(word in combined_context for word in [
            "cleared cache", "clear cache",
            "cleared temporary files"
        ]):
            attempted_steps.append("cache")

        # Filter attempted instructions from retrieved articles.
        filtered_articles = []

        for article in retrieved_articles:
            original_content = article.get("content", "")
            filtered_lines = []

            for line in original_content.splitlines():
                normalized_line = line.lower().strip()

                if "restart" in attempted_steps and "restart" in normalized_line:
                    continue

                if "update" in attempted_steps and (
                    "update" in normalized_line
                    or "up to date" in normalized_line
                ):
                    continue

                if "cache" in attempted_steps and "cache" in normalized_line:
                    continue

                filtered_lines.append(line)

            filtered_content = "\n".join(filtered_lines).strip()
            filtered_content = filtered_content.replace("Checkwhether", "Check whether")
            
            if filtered_content:
                filtered_articles.append({
                    **article,
                    "content": filtered_content
                })

        # Build filtered knowledge for the LLM.
        filtered_knowledge = {
            "found": len(filtered_articles) > 0,
            "results": filtered_articles
        }

        # Prepare the remaining proposed solution.
        proposed_solution = "\n".join(
            article["content"]
            for article in filtered_articles
        )

        # TOOL 3: Validate the remaining solution.
        validation = {
            "valid": False,
            "reason": "No relevant unattempted technical solution was retrieved."
        }

        if proposed_solution:
            validation_result = await self.kernel.invoke(
                plugin_name="Technical",
                function_name="validate_technical_solution",
                solution=proposed_solution,
            )

            validation = parse_tool_result(validation_result)

            print("\n[TOOL EXECUTED] validate_technical_solution")
            print(validation)

        verified_results = {
            "severity": severity,
            "technical_knowledge": filtered_knowledge,
            "solution_validation": validation,
            "previously_attempted_steps": attempted_steps
        }

        # Generate exactly one customer-facing response.
        prompt = f"""
        You are an enterprise technical support specialist.

        CUSTOMER MESSAGE:
        {customer_message}

        PREVIOUS CUSTOMER CONVERSATIONS:
        {json.dumps(conversation_history, indent=2)}

        VERIFIED INVESTIGATION RESULTS:
        {json.dumps(verified_results, indent=2)}

        STRICT INSTRUCTIONS:

        1. Write exactly ONE customer-facing response.
        2. Do not produce an internal technical report.
        3. Do not repeat the response or provide multiple versions.
        4. Do not recommend any previously attempted troubleshooting step.
        5. Use only the remaining troubleshooting instructions in the verified FAQ.
        6. If no useful unattempted instruction remains, explain this politely.
        7. If further troubleshooting is needed, recommend collecting the relevant
        error message and escalating to technical support when supported by the FAQ.
        8. Never claim that the issue is fixed without evidence.
        9. Never claim that an escalation or repair has already happened.
        10. Do not mention internal tools, agents, JSON, confidence scores,
            or investigation procedures.
        11. Use professional, clear English.
        12. Do not include placeholders such as [Company Name] or [Support Team].

        OUTPUT FORMAT:

        Hello,

        [Brief acknowledgement and relevant troubleshooting guidance.]

        [Explain the next step or escalation recommendation.]

        Best regards,
        Customer Support Team

        Return only the customer-facing response.
        """


        response_parts = []

        async for response in self.agent.invoke(messages=prompt):

            content = getattr(response, "content", None)

            # Case 1: Direct string response.
            if isinstance(content, str):
                response_parts.append(content)

            # Case 2: Semantic Kernel ChatMessageContent.
            elif content is not None:

                # Extract text from content items.
                items = getattr(content, "items", [])

                for item in items:
                    text = getattr(item, "text", None)

                    if text:
                        response_parts.append(text)

                # Fallback: extract from the underlying Ollama response.
                if not response_parts:
                    inner = getattr(content, "inner_content", None)
                    message = getattr(inner, "message", None)
                    raw_text = getattr(message, "content", None)

                    if raw_text:
                        response_parts.append(raw_text)

            # Case 3: Direct text property.
            if not response_parts:
                raw_text = getattr(response, "text", None)

                if raw_text:
                    response_parts.append(raw_text)


        final_response = "\n".join(response_parts).strip()

        if not final_response:
            print("\n[DEBUG] Empty response detected.")
            print("[DEBUG] Response object:", repr(response))
            print("[DEBUG] Response content:", repr(
                getattr(response, "content", None)
            ))

            raise RuntimeError(
                "Technical Specialist generated an empty response."
            )

        return final_response



async def main():

    agent = LLMTechnicalAgent()

    customer_message = (
        "My application crashes whenever I open it. "
        "I have restarted it but the problem continues."
    )

    print("\n===== LLM TECHNICAL SPECIALIST =====")
    print("\nCustomer:", customer_message)

    result = await agent.investigate(customer_message)

    print("\n===== TECHNICAL INVESTIGATION RESULT =====")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
