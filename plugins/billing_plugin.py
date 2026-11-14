
import json

from semantic_kernel.functions import kernel_function
from tools.billing_tools import (
    search_billing_policy,
    check_transaction,
    evaluate_duplicate_payment
)


class BillingPlugin:

    def __init__(self):
        # Preserve the same demonstration data as BillingSpecialistAgent.
        self.transaction_store = {
            "TXN1001": {
                "amount": 1500,
                "status": "duplicate_verified",
                "currency": "INR"
            },
            "TXN1002": {
                "amount": 999,
                "status": "successful",
                "currency": "INR"
            }
        }

    @kernel_function(
        name="search_billing_policy",
        description="Search the billing policy knowledge base."
    )
    def search_policy(self, query: str) -> str:
        result = search_billing_policy(query)
        return json.dumps(result)

    @kernel_function(
        name="check_transaction",
        description="Look up a transaction using its transaction ID."
    )
    def transaction_lookup(self, transaction_id: str) -> str:
        result = check_transaction(
            transaction_id,
            self.transaction_store
        )
        return json.dumps(result)

    @kernel_function(
        name="evaluate_duplicate_payment",
        description="Evaluate whether a transaction is a verified duplicate."
    )
    def evaluate_duplicate(self, transaction_json: str) -> str:
        transaction = json.loads(transaction_json)
        result = evaluate_duplicate_payment(transaction)
        return json.dumps(result)
