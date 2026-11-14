
from orchestration.support_manager import SupportManager


def test_billing_workflow():

    manager = SupportManager()

    result = manager.process_ticket(
        "CUST001",
        "I was charged twice for my subscription.",
        "TXN1001"
    )

    assert result.category == "billing"
    assert result.status == "resolved"


def test_technical_workflow():

    manager = SupportManager()

    result = manager.process_ticket(
        "CUST002",
        "My application keeps crashing."
    )

    assert result.category == "technical"
    assert result.status == "resolved"


def test_account_workflow():

    manager = SupportManager()

    result = manager.process_ticket(
        "CUST001",
        "I cannot login to my account."
    )

    assert result.category == "account"
    assert result.status == "resolved"


def test_locked_account_escalation():

    manager = SupportManager()

    result = manager.process_ticket(
        "CUST002",
        "My account is locked."
    )

    assert result.status == "escalated"
    assert result.human_review_status == "pending"


def test_unknown_ticket_escalation():

    manager = SupportManager()

    result = manager.process_ticket(
        "CUST001",
        "I have a question about something unusual."
    )

    assert result.status == "escalated"
    assert result.human_review_status == "pending"
