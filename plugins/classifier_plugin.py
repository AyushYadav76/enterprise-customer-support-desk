
import json

from semantic_kernel.functions import kernel_function

from tools.classifier_tools import (
    validate_ticket,
    classify_ticket_by_rules,
)


class ClassifierPlugin:
    """Semantic Kernel plugin for ticket validation and classification."""

    @kernel_function(
        name="validate_support_ticket",
        description="Validate a support ticket message and customer ID."
    )
    def validate_support_ticket(
        self,
        message: str,
        customer_id: str
    ) -> str:

        result = validate_ticket(message, customer_id)
        return json.dumps(result)

    @kernel_function(
        name="classify_support_ticket",
        description="Classify a ticket into billing, technical, account, or other."
    )
    def classify_support_ticket(self, message: str) -> str:

        result = classify_ticket_by_rules(message)
        return json.dumps(result)
