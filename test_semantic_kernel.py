
import asyncio

from semantic_kernel import Kernel
from plugins.classifier_plugin import ClassifierPlugin


async def main():
    # Initialize Semantic Kernel
    kernel = Kernel()

    # Register the classifier plugin
    kernel.add_plugin(
        ClassifierPlugin(),
        plugin_name="Classifier"
    )

    print("Semantic Kernel initialized successfully.")
    print("Registered plugins:", list(kernel.plugins.keys()))

    # Test 1: Validate a support ticket
    validation_result = await kernel.invoke(
        plugin_name="Classifier",
        function_name="validate_support_ticket",
        message="I was charged twice for my subscription.",
        customer_id="CUST001"
    )

    print("\n--- Ticket Validation ---")
    print(validation_result)

    # Test 2: Classify a support ticket
    classification_result = await kernel.invoke(
        plugin_name="Classifier",
        function_name="classify_support_ticket",
        message="I was charged twice for my subscription."
    )

    print("\n--- Ticket Classification ---")
    print(classification_result)


if __name__ == "__main__":
    asyncio.run(main())
