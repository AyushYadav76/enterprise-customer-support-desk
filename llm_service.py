
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.ollama import (
    OllamaChatCompletion,
    OllamaChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory


MODEL_NAME = "support-desk-ai"
OLLAMA_HOST = "http://localhost:11434"
SERVICE_ID = "local-ollama"


def create_kernel() -> Kernel:
    """Create a Semantic Kernel instance using local Ollama."""

    kernel = Kernel()

    ollama_service = OllamaChatCompletion(
        service_id=SERVICE_ID,
        ai_model_id=MODEL_NAME,
        host=OLLAMA_HOST,
    )

    kernel.add_service(ollama_service)

    return kernel


async def ask_local_model(prompt: str) -> str:
    """Generate a response through Semantic Kernel and Ollama."""

    kernel = create_kernel()
    chat_service = kernel.get_service(SERVICE_ID)

    history = ChatHistory(
        system_message=(
            "You are an enterprise customer support AI assistant. "
            "Always respond in English. "
            "Be professional, clear, and concise. "
            "Never invent transaction or customer information."
        )
    )

    history.add_user_message(prompt)

    # Semantic Kernel 1.47.0 requires explicit execution settings.
    execution_settings = OllamaChatPromptExecutionSettings(
        service_id=SERVICE_ID,
        options={
            "temperature": 0.3,
        },
    )

    response = await chat_service.get_chat_message_content(
        chat_history=history,
        settings=execution_settings,
        kernel=kernel,
    )

    return response.content or str(response)


if __name__ == "__main__":
    import asyncio

    async def main():
        prompt = (
            "A customer says they were charged twice "
            "for their subscription. Explain how you "
            "would investigate this issue."
        )

        print("\n===== SEMANTIC KERNEL + OLLAMA =====\n")

        response = await ask_local_model(prompt)

        print(response)

    asyncio.run(main())
