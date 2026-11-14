
import re


def validate_ticket(message: str, customer_id: str) -> dict:
    """Validate incoming support ticket information."""

    if not customer_id or not customer_id.strip():
        return {
            "valid": False,
            "reason": "Customer ID is missing."
        }

    if not message or not message.strip():
        return {
            "valid": False,
            "reason": "Ticket message is empty."
        }

    if len(message.strip()) < 5:
        return {
            "valid": False,
            "reason": "Ticket message is too short."
        }

    return {
        "valid": True,
        "reason": "Ticket information is valid."
    }


def classify_ticket_by_rules(message: str) -> dict:
    """Classify a ticket using predefined keyword rules."""

    text = message.lower()

    keywords = {
        "billing": [
            "payment", "refund", "invoice", "charged",
            "subscription", "transaction", "bill",
            "double charge", "money"
        ],

        "technical": [
            "error", "bug", "crash", "crashing",
            "crashed", "crashes", "not working",
            "slow", "server", "loading", "broken",
            "installation", "technical", "freezing",
            "freeze", "hang", "hanging"
        ],

        "account": [
            "login", "password", "sign in",
            "locked", "account", "authentication",
            "verification", "access"
        ]
    }

    scores = {}

    for category, words in keywords.items():
        scores[category] = sum(
            1 for word in words
            if re.search(
                r"\b" + re.escape(word) + r"\b",
                text
            )
        )

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score == 0:
        return {
            "category": "other",
            "confidence": 0.50,
            "reason": "No matching category keywords found."
        }

    total_matches = sum(scores.values())

    confidence = min(
        0.95,
        0.70 + (best_score - 1) * 0.10
    )

    if list(scores.values()).count(best_score) > 1:
        return {
            "category": "other",
            "confidence": 0.40,
            "reason": "Multiple categories have equal scores."
        }

    if total_matches > best_score:
        confidence = min(confidence, 0.65)

    return {
        "category": best_category,
        "confidence": round(confidence, 2),
        "reason": f"Matched {best_score} keyword(s) for {best_category}."
    }
