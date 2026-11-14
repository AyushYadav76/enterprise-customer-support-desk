
from shared_state import TicketState
from agents.classifier_agent import ClassifierAgent


def test_billing_classification():

    ticket = TicketState(
        customer_id="CUST001",
        message="I was charged twice for my subscription."
    )

    result = ClassifierAgent().run(ticket)

    assert result.category == "billing"
    assert result.assigned_specialist == "Billing Specialist"
    assert result.status == "classified"


def test_technical_classification():

    ticket = TicketState(
        customer_id="CUST002",
        message="My application keeps crashing."
    )

    result = ClassifierAgent().run(ticket)

    assert result.category == "technical"
    assert result.assigned_specialist == "Technical Specialist"


def test_account_classification():

    ticket = TicketState(
        customer_id="CUST003",
        message="I cannot login because my password is locked."
    )

    result = ClassifierAgent().run(ticket)

    assert result.category == "account"
    assert result.assigned_specialist == "Account Specialist"


def test_invalid_ticket():

    ticket = TicketState(
        customer_id="CUST004",
        message="Hi"
    )

    result = ClassifierAgent().run(ticket)

    assert result.status == "invalid"
