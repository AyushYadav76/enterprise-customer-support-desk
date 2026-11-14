import nbformat as nbf
from pathlib import Path

notebook = nbf.v4.new_notebook()

notebook["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3 (venv)",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.13"
    }
}

cells = []

cells.append(nbf.v4.new_markdown_cell("""# Enterprise Customer Support Triage and Resolution Desk

## Multi-Agent System Demonstration

This notebook demonstrates the actual LLM-powered multi-agent customer support system.

**Architecture:** Classifier Agent → Specialist Agent → Escalation Router

**Specialists demonstrated:**
- Billing Specialist
- Technical Specialist
- Account Specialist

The system uses local Ollama models, Python tools, conversation memory, and an append-only JSONL execution log.

Run the cells sequentially. Ollama must be running locally and the configured model must be available.
"""))

cells.append(nbf.v4.new_markdown_cell("""## 1. Environment Setup

The notebook locates the project root and imports the existing orchestration manager. It does not recreate or simulate any agents.
"""))

cells.append(nbf.v4.new_code_cell("""import sys
from pathlib import Path

# Locate the project root whether Jupyter starts in the root or notebooks folder.
current = Path.cwd().resolve()

project_root = next(
    (p for p in [current, *current.parents] if (p / "orchestration").is_dir()),
    None
)

if project_root is None:
    raise RuntimeError("Could not locate the project root containing the orchestration folder.")

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Project root:", project_root)
"""))

cells.append(nbf.v4.new_code_cell("""import asyncio
import json
from IPython.display import display, Markdown

from orchestration.llm_support_manager import LLMSupportManager

manager = LLMSupportManager()

print("LLM Support Manager initialized successfully.")
print("Run log:", manager.run_log_path)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 2. Ticket Execution and Trace Display

The following helper calls the real asynchronous `process_ticket()` method and displays the returned ticket fields and actual agent execution trace.
"""))

cells.append(nbf.v4.new_code_cell("""async def run_demo_ticket(customer_id, message, transaction_id=None):
    ticket = await manager.process_ticket(
        customer_id=customer_id,
        message=message,
        transaction_id=transaction_id
    )

    print("=" * 75)
    print("TICKET SUMMARY")
    print("=" * 75)
    print("Ticket ID:", ticket.ticket_id)
    print("Customer ID:", ticket.customer_id)
    print("Message:", ticket.message)
    print("Category:", ticket.category)
    print("Confidence:", ticket.confidence)
    print("Assigned Specialist:", ticket.assigned_specialist)
    print("Final Status:", ticket.status)
    print("Resolution:", ticket.resolution)
    print("\\nCUSTOMER-FACING RESPONSE:")
    print(ticket.drafted_reply or "No response drafted.")

    if ticket.escalation_reason:
        print("\\nESCALATION REASON:")
        print(ticket.escalation_reason)

    print("\\nAGENT EXECUTION TRACE:")
    for index, entry in enumerate(ticket.agent_trace, start=1):
        print(f"\\n{index}. {entry.agent_name}")
        print("   Status:", entry.status)
        print("   Timestamp:", entry.timestamp)
        print("   Output:", entry.output)

    print("\\nPrevious conversations retrieved:", len(ticket.conversation_history))
    print("=" * 75)

    return ticket
"""))

cells.append(nbf.v4.new_markdown_cell("""## 3. Scenario A — Billing Support

A customer reports a duplicate payment. The Billing Specialist receives the transaction ID and uses the existing billing tools to investigate it.

The demonstration transaction `TXN1001` is the sample transaction configured in the project's billing tools. Eligibility for refund review must not be interpreted as an approved or processed refund.
"""))

cells.append(nbf.v4.new_code_cell("""billing_ticket = await run_demo_ticket(
    customer_id="CUST_BILLING_DEMO",
    message="I was charged twice for my subscription. Please investigate the duplicate payment.",
    transaction_id="TXN1001"
)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 4. Scenario B — Technical Support

A customer reports that the application keeps crashing. The Technical Specialist uses the technical knowledge base and its existing tools to investigate and draft a response.
"""))

cells.append(nbf.v4.new_code_cell("""technical_ticket = await run_demo_ticket(
    customer_id="CUST_TECH_DEMO",
    message="My application keeps crashing even after restarting. Please help me resolve this issue."
)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 5. Scenario C — Account Support and Escalation

This scenario uses sample account `CUST002`, which is configured as locked in the project's account tool data. The account specialist verifies access, and the escalation router handles cases that require human support.
"""))

cells.append(nbf.v4.new_code_cell("""account_ticket = await run_demo_ticket(
    customer_id="CUST002",
    message="I cannot access my account because it is locked. Please help me regain access."
)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 6. Compare the Three Ticket Outcomes

This summary is derived from the actual ticket objects returned by the manager.
"""))

cells.append(nbf.v4.new_code_cell("""demo_tickets = [
    billing_ticket,
    technical_ticket,
    account_ticket
]

for ticket in demo_tickets:
    print({
        "ticket_id": ticket.ticket_id,
        "category": ticket.category,
        "specialist": ticket.assigned_specialist,
        "status": ticket.status,
        "escalation_required": bool(ticket.escalation_reason)
    })
"""))

cells.append(nbf.v4.new_markdown_cell("""## 7. Conversation Memory Demonstration

Submit a follow-up from the same technical customer. The manager retrieves previous conversations for that customer and includes them in the ticket context.
"""))

cells.append(nbf.v4.new_code_cell("""technical_followup = await run_demo_ticket(
    customer_id="CUST_TECH_DEMO",
    message="The application is still crashing. What should I try next?"
)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 8. Append-Only Execution Log

The manager writes each processed ticket to `logs/llm_agent_runs.jsonl`. The following cell reads the latest records without modifying the log.
"""))

cells.append(nbf.v4.new_code_cell("""log_path = project_root / "logs" / "llm_agent_runs.jsonl"

if log_path.exists():
    with log_path.open("r", encoding="utf-8") as file:
        log_lines = file.readlines()

    print("Total log records:", len(log_lines))

    for line in log_lines[-4:]:
        record = json.loads(line)
        ticket_data = record.get("ticket", {})
        print({
            "timestamp": record.get("timestamp"),
            "ticket_id": ticket_data.get("ticket_id"),
            "category": ticket_data.get("category"),
            "status": ticket_data.get("status")
        })
else:
    print("Execution log not found:", log_path)
"""))

cells.append(nbf.v4.new_markdown_cell("""## 9. Demonstration Conclusions

This demonstration exercises the implemented multi-agent workflow:

1. The Classifier Agent validates and categorizes incoming tickets.
2. The Support Manager routes tickets to the relevant specialist.
3. Billing, Technical, and Account Specialists use their respective tools.
4. Conversation Memory retrieves previous interactions for the same customer.
5. The Escalation Router handles cases requiring human intervention.
6. The Support Manager records the execution trace and appends the ticket to the JSONL run log.

**Note:** The outputs shown in this notebook are generated by the running application. They may vary depending on the local model response and the current conversation history.
"""))

notebook.cells = cells

output_path = Path("notebooks") / "Customer_Support_Multi_Agent_Demo.ipynb"
output_path.parent.mkdir(parents=True, exist_ok=True)

nbf.write(notebook, output_path)

print("Notebook created successfully:", output_path.resolve())
print("Total cells:", len(notebook.cells))
