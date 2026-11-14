# Enterprise Customer Support Triage and Resolution Desk

## 1. Project Overview

An AI-powered multi-agent system that validates, classifies, routes, and investigates customer support tickets. It combines specialized agents, Python tools, Retrieval-Augmented Generation (RAG), conversation memory, and human escalation.

**Stack:** Python, Microsoft Semantic Kernel, Ollama, SQLite, ChromaDB, Pydantic, Pytest.

## 2. Architecture and Agents

The system follows a **Router-to-Specialists** architecture coordinated by the LLM Support Manager.

| Component | Responsibility |
|---|---|
| LLM Support Manager | Coordinates ticket processing and agent execution. |
| LLM Classifier Agent | Validates tickets and identifies category and confidence. |
| Billing Specialist | Investigates payment issues using policies and transaction tools. |
| Technical Specialist | Retrieves relevant FAQs through RAG, checks severity, and validates solutions. |
| Account Specialist | Looks up accounts and verifies access. |
| Escalation Router | Routes unresolved or critical cases for human review. |
| Conversation Memory | Retrieves previous customer interactions from SQLite. |

Each specialist uses dedicated Python tools. Agent execution is recorded in an append-only JSONL run log. See `architecture.mmd` for the architecture diagram.

## 3. Technical Implementation

- **LLM:** Local Ollama model `support-desk-ai`.
- **Agent framework:** Microsoft Semantic Kernel.
- **Technical RAG:** FAQ documents are embedded using `nomic-embed-text`, stored in persistent ChromaDB, and retrieved using cosine similarity. The system retrieves up to three relevant articles with a minimum similarity threshold of 0.60.
- **Conversation memory:** SQLite stores ticket history and retrieves previous interactions for the same customer.
- **Tools:** Python functions for ticket validation, classification, billing investigation, technical retrieval, account verification, and escalation.
- **Testing:** Pytest.

## 4. Project Structure

```text
customer-support-desk/
├── agents/              # Classifier and specialist agents
├── tools/               # Python tool functions
├── plugins/             # Semantic Kernel plugins
├── orchestration/       # LLM Support Manager
├── knowledge_base/      # Billing policies and technical FAQs
├── memory/              # SQLite and ChromaDB data
├── logs/                # Append-only execution logs
├── notebooks/            # Multi-agent demonstration
├── tests/                # Automated tests
├── architecture.mmd
├── config.py
├── shared_state.py
├── Modelfile
├── requirements.txt
└── README.md
```

## 5. Installation and Setup

**Prerequisites:** Python 3.11+, VS Code, and Ollama.

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Ensure both required Ollama models are available:

```powershell
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
ollama create support-desk-ai -f Modelfile
ollama list
```

Keep the Ollama service running while using the project. Do not commit `.env` files, API keys, or credentials.

## 6. Running the Demonstration

Open the project:

```powershell
code .
```

Open `notebooks/Customer_Support_Multi_Agent_Demo.ipynb`, select the project's virtual environment as the notebook kernel, and execute the cells sequentially.

The notebook demonstrates:
- Duplicate-payment investigation.
- Technical issue investigation using RAG.
- Locked-account escalation.
- Conversation memory and follow-up tickets.
- Agent execution traces and run logging.

## 7. Testing

Run the automated tests:

```powershell
python -m pytest tests/ -v
```

The deterministic test suite has previously passed **29 tests**. Additional integration demonstrations are available in the root-level `test_integrated_*.py` scripts.

## 8. Limitations and Future Improvements

- Account and transaction records currently use sample data.
- Refund eligibility does not mean a refund has been approved or processed.
- Human escalation uses an application-level review queue.
- Classification uses rule-based signals supported by LLM-generated explanations.
- Production deployment would require secure authentication, enterprise integrations, monitoring, and stronger data protection.

## 9. Conclusion

The project demonstrates a coordinated multi-agent customer support workflow with specialist investigation, Python tool execution, semantic knowledge retrieval, conversation memory, human escalation, and traceable ticket processing.