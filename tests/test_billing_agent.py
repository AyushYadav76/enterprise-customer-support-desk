
from shared_state import TicketState

from agents.classifier_agent import ClassifierAgent
from agents.billing_agent import BillingSpecialistAgent


def create_billing_ticket():

    ticket = TicketState(
        customer_id="CUST001",
        message="I was charged twice for my subscription."
    )

    return ClassifierAgent().run(ticket)


def test_verified_duplicate_payment():

    ticket = create_billing_ticket()

    result = BillingSpecialistAgent().run(
        ticket,
        "TXN1001"
    )

    assert result.status == "resolved"
    assert "Verified duplicate payment" in result.resolution


def test_missing_transaction():

    ticket = create_billing_ticket()

    result = BillingSpecialistAgent().run(
        ticket,
        "TXN9999"
    )

    assert result.status == "needs_escalation"


def test_missing_transaction_id():

    ticket = create_billing_ticket()

    result = BillingSpecialistAgent().run(ticket)

    assert result.status == "needs_escalation"


def test_non_billing_ticket():

    ticket = TicketState(
        customer_id="CUST002",
        message="My application keeps crashing."
    )

    ticket = ClassifierAgent().run(ticket)

    result = BillingSpecialistAgent().run(ticket)

    assert result.status == "classified"
