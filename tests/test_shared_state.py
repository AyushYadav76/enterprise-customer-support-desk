
from shared_state import TicketState


def test_ticket_creation():

    ticket = TicketState(
        customer_id="CUST001",
        message="Unable to log in"
    )

    assert ticket.customer_id == "CUST001"
    assert ticket.status == "received"
    assert ticket.ticket_id is not None


def test_agent_trace():

    ticket = TicketState(
        customer_id="CUST002",
        message="Payment failed"
    )

    ticket.add_trace(
        "Classifier Agent",
        "completed",
        "Billing issue detected"
    )

    assert len(ticket.agent_trace) == 1
    assert ticket.agent_trace[0].agent_name == "Classifier Agent"


def test_ticket_status_update():

    ticket = TicketState(
        customer_id="CUST003",
        message="Account locked"
    )

    ticket.update_status("in_progress")

    assert ticket.status == "in_progress"
