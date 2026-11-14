
import asyncio
import json

from semantic_kernel import Kernel

from plugins.classifier_plugin import ClassifierPlugin
from plugins.billing_plugin import BillingPlugin
from plugins.technical_plugin import TechnicalPlugin
from plugins.account_plugin import AccountPlugin
from plugins.escalation_plugin import EscalationPlugin


async def main():

    kernel = Kernel()

    # Register all five plugins.
    kernel.add_plugin(ClassifierPlugin(), plugin_name="Classifier")
    kernel.add_plugin(BillingPlugin(), plugin_name="Billing")
    kernel.add_plugin(TechnicalPlugin(), plugin_name="Technical")
    kernel.add_plugin(AccountPlugin(), plugin_name="Account")
    kernel.add_plugin(EscalationPlugin(), plugin_name="Escalation")

    print("REGISTERED PLUGINS")
    print(list(kernel.plugins.keys()))

    # 1. Classifier
    result = await kernel.invoke(
        plugin_name="Classifier",
        function_name="classify_support_ticket",
        message="I was charged twice for my subscription."
    )
    print("\n1. CLASSIFIER")
    print(result)

    # 2. Billing policy search
    result = await kernel.invoke(
        plugin_name="Billing",
        function_name="search_billing_policy",
        query="duplicate payment"
    )
    print("\n2. BILLING POLICY")
    print(result)

    # 3. Transaction lookup
    result = await kernel.invoke(
        plugin_name="Billing",
        function_name="check_transaction",
        transaction_id="TXN1001"
    )
    print("\n3. TRANSACTION LOOKUP")
    print(result)

    # 4. Technical knowledge search
    result = await kernel.invoke(
        plugin_name="Technical",
        function_name="search_technical_knowledge",
        query="application crashes"
    )
    print("\n4. TECHNICAL KNOWLEDGE")
    print(result)

    # 5. Technical severity check
    result = await kernel.invoke(
        plugin_name="Technical",
        function_name="check_error_severity",
        message="The application crashes whenever I open it."
    )
    print("\n5. TECHNICAL SEVERITY")
    print(result)

    # 6. Account lookup
    result = await kernel.invoke(
        plugin_name="Account",
        function_name="lookup_account",
        customer_id="CUST001"
    )
    print("\n6. ACCOUNT LOOKUP")
    print(result)

    # 7. Escalation check
    result = await kernel.invoke(
        plugin_name="Escalation",
        function_name="check_escalation_required",
        confidence=0.55,
        status="needs_escalation",
        threshold=0.70
    )
    print("\n7. ESCALATION CHECK")
    print(result)

    print("\nALL PLUGIN INVOCATIONS COMPLETED.")


if __name__ == "__main__":
    asyncio.run(main())
