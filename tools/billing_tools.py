
def search_billing_policy(query: str) -> dict:
    """Search the billing policy document."""

    path = "knowledge_base/billing_policy.txt"

    with open(path, "r", encoding="utf-8") as file:
        content = file.read()

    sections = content.split("POLICY ")

    matches = []

    for section in sections:
        if any(
            word.lower() in section.lower()
            for word in query.split()
            if len(word) > 3
        ):
            matches.append(section.strip())

    return {
        "found": len(matches) > 0,
        "policies": matches
    }


def check_transaction(
    transaction_id: str,
    transaction_store: dict
) -> dict:
    """Check a transaction in the demonstration transaction store."""

    if transaction_id not in transaction_store:
        return {
            "found": False,
            "reason": "Transaction not found."
        }

    return {
        "found": True,
        "transaction": transaction_store[transaction_id]
    }


def evaluate_duplicate_payment(transaction: dict) -> dict:
    """Check whether a transaction represents a verified duplicate."""

    if not transaction:
        return {
            "eligible": False,
            "reason": "Transaction information unavailable."
        }

    if transaction.get("status") != "duplicate_verified":
        return {
            "eligible": False,
            "reason": "Duplicate payment has not been verified."
        }

    return {
        "eligible": True,
        "reason": "Duplicate payment verified. Eligible for refund review."
    }
