
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    agent_name: str
    status: str
    output: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )


class TicketState(BaseModel):
    ticket_id: str = Field(
        default_factory=lambda: str(uuid4())
        
    )

    customer_id: str
    message: str

    category: Optional[str] = None
    confidence: float = 0.0

    assigned_specialist: Optional[str] = None

    status: str = "received"

    resolution: Optional[str] = None
    drafted_reply: Optional[str] = None

    escalation_reason: Optional[str] = None

    human_review_status: Optional[str] = None
    human_review_decision: Optional[str] = None
    human_review_notes: Optional[str] = None

    retrieved_sources: list[str] = Field(
        default_factory=list
    )

    conversation_history: list[str] = Field(
        default_factory=list
    )

    agent_trace: list[AgentResult] = Field(
        default_factory=list
    )

    def add_trace(
        self,
        agent_name: str,
        status: str,
        output: str
    ):
        result = AgentResult(
            agent_name=agent_name,
            status=status,
            output=output
        )

        self.agent_trace.append(result)

    def update_status(self, new_status: str):
        self.status = new_status


if __name__ == "__main__":

    ticket = TicketState(
        customer_id="CUST001",
        message="I was charged twice for my subscription."
    )

    ticket.add_trace(
        agent_name="Classifier Agent",
        status="completed",
        output="Billing issue detected"
    )

    print("\nTicket Created Successfully")
    print(ticket.model_dump_json(indent=4))
