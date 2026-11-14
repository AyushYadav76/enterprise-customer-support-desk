
import pytest

from shared_state import TicketState
from agents.escalation_router import EscalationRouter


def create_ticket(status="needs_escalation", confidence=0.9):

    return TicketState(
        customer_id="CUST100",
        message="My account needs support.",
        category="account",
        confidence=confidence,
        status=status
    )


def test_escalation_required():

    ticket = create_ticket()

    router = EscalationRouter()

    result = router.run(ticket)

    assert result.status == "escalated"
    assert result.human_review_status == "pending"
    assert len(router.human_review_queue) == 1


def test_low_confidence_escalation():

    ticket = create_ticket(
        status="classified",
        confidence=0.3
    )

    result = EscalationRouter().run(ticket)

    assert result.status == "escalated"


def test_no_escalation_required():

    ticket = create_ticket(
        status="resolved",
        confidence=0.9
    )

    result = EscalationRouter().run(ticket)

    assert result.status == "resolved"


def test_human_review_completion():

    ticket = create_ticket()

    router = EscalationRouter()

    ticket = router.run(ticket)

    ticket = router.review_ticket(
        ticket,
        "resolved",
        "Issue resolved by human support."
    )

    assert ticket.status == "resolved"
    assert ticket.human_review_status == "completed"


def test_invalid_human_decision():

    ticket = create_ticket()

    router = EscalationRouter()

    with pytest.raises(ValueError):

        router.review_ticket(
            ticket,
            "invalid_decision",
            "Test notes"
        )
