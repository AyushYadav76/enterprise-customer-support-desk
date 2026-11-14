
# Demonstration account database
ACCOUNT_STORE = {
    "CUST001": {
        "status": "active",
        "email_verified": True,
        "locked": False
    },
    "CUST002": {
        "status": "locked",
        "email_verified": True,
        "locked": True
    },
    "CUST003": {
        "status": "active",
        "email_verified": False,
        "locked": False
    }
}


def lookup_account(customer_id: str) -> dict:
    """Retrieve customer account information."""

    account = ACCOUNT_STORE.get(customer_id)

    if not account:
        return {
            "found": False,
            "reason": "Account not found."
        }

    return {
        "found": True,
        "account": account
    }


def verify_account_access(account: dict) -> dict:
    """Check whether account access is available."""

    if account.get("locked"):
        return {
            "accessible": False,
            "reason": "Account is locked."
        }

    if not account.get("email_verified"):
        return {
            "accessible": False,
            "reason": "Email verification is required."
        }

    return {
        "accessible": True,
        "reason": "Account is active and verified."
    }


def generate_account_guidance(account: dict) -> str:
    """Generate appropriate account support instructions."""

    if account.get("locked"):
        return (
            "Your account is currently locked. "
            "Please contact account support for verification."
        )

    if not account.get("email_verified"):
        return (
            "Please complete email verification "
            "before accessing your account."
        )

    return (
        "Your account is active. "
        "If login problems continue, reset your password "
        "and try again."
    )
