
import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv(
    "APP_NAME",
    "Customer Support Triage Desk"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)

CONFIDENCE_THRESHOLD = float(
    os.getenv("CONFIDENCE_THRESHOLD", "0.70")
)

DATABASE_PATH = "memory/support_memory.db"

KNOWLEDGE_BASE_PATH = "knowledge_base"

LOG_DIRECTORY = "logs"
