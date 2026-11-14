
from shared_state import TicketState

from agents.classifier_agent import ClassifierAgent
from agents.technical_agent import TechnicalSpecialistAgent


def create_technical_ticket(message):

    ticket = TicketState(
        customer_id="CUST100",
        message=message
    )

    return ClassifierAgent().run(ticket)


def test_application_crash():

    ticket = create_technical_ticket(
        "My application keeps crashing."
    )

    result = TechnicalSpecialistAgent().run(ticket)

    assert result.status == "resolved"
    assert result.resolution is not None


def test_website_not_loading():

    ticket = create_technical_ticket(
        "My website is not loading."
    )

    result = TechnicalSpecialistAgent().run(ticket)

    assert result.status == "resolved"


def test_critical_technical_issue():

    ticket = create_technical_ticket(
        "Our system has database corruption."
    )

    result = TechnicalSpecialistAgent().run(ticket)

    assert result.status == "needs_escalation"


def test_non_technical_ticket():

    ticket = TicketState(
        customer_id="CUST101",
        message="I need a refund for my payment."
    )

    ticket = ClassifierAgent().run(ticket)

    result = TechnicalSpecialistAgent().run(ticket)

    assert result.status == "classified"
