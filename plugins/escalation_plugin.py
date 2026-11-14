
import json

from semantic_kernel.functions import kernel_function
from tools.escalation_tools import (
    check_escalation_required,
    create_human_review_record,
    submit_human_decision
)


class EscalationPlugin:

    @kernel_function(
        name="check_escalation_required",
        description="Determine whether a ticket needs human review."
    )
    def check_escalation(
        self,
        confidence: float,
        status: str,
        threshold: float
    ) -> str:
        result = check_escalation_required(
            confidence,
            status,
            threshold
        )
        return json.dumps(result)

    @kernel_function(
        name="create_human_review_record",
        description="Create a record for a ticket requiring human review."
    )
    def create_review_record(
        self,
        ticket_id: str,
        customer_id: str,
        message: str,
        reason: str
    ) -> str:
        result = create_human_review_record(
            ticket_id,
            customer_id,
            message,
            reason
        )
        return json.dumps(result)

    @kernel_function(
        name="submit_human_decision",
        description="Validate a human review decision and its notes."
    )
    def submit_decision(
        self,
        decision: str,
        notes: str
    ) -> str:
        result = submit_human_decision(decision, notes)
        return json.dumps(result)
