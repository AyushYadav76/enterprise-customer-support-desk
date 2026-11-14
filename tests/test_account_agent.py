
from shared_state import TicketState

from agents.classifier_agent import ClassifierAgent
from agents.account_agent import AccountSpecialistAgent


def create_account_ticket(customer_id, message):

    ticket = TicketState(
        customer_id=customer_id,
        message=message
    )

    return ClassifierAgent().run(ticket)


def test_active_account():

    ticket = create_account_ticket(
        "CUST001",
        "I cannot login to my account."
    )

    result = AccountSpecialistAgent().run(ticket)

    assert result.status == "resolved"


def test_locked_account():

    ticket = create_account_ticket(
        "CUST002",
        "My account is locked."
    )

    result = AccountSpecialistAgent().run(ticket)

    assert result.status == "needs_escalation"


def test_unverified_email():

    ticket = create_account_ticket(
        "CUST003",
        "I cannot access my account."
    )

    result = AccountSpecialistAgent().run(ticket)

    assert result.status == "needs_escalation"


def test_non_account_ticket():

    ticket = TicketState(
        customer_id="CUST001",
        message="I need a refund for my payment."
    )

    ticket = ClassifierAgent().run(ticket)

    result = AccountSpecialistAgent().run(ticket)

    assert result.status == "classified"
