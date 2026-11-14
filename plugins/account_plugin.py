
import json

from semantic_kernel.functions import kernel_function

from tools.account_tools import (
    lookup_account,
    verify_account_access,
    generate_account_guidance,
)


class AccountPlugin:

    @kernel_function(
        name="lookup_account",
        description="Look up a customer account using the customer ID."
    )
    def lookup_customer_account(self, customer_id: str) -> str:
        result = lookup_account(customer_id)
        return json.dumps(result)

    @kernel_function(
        name="verify_account_access",
        description="Verify access using the retrieved account data."
    )
    def verify_customer_access(self, account_json: str) -> str:
        account = json.loads(account_json)
        result = verify_account_access(account)
        return json.dumps(result)

    @kernel_function(
        name="generate_account_guidance",
        description="Generate account troubleshooting guidance."
    )
    def generate_customer_guidance(self, account_json: str) -> str:
        account = json.loads(account_json)
        result = generate_account_guidance(account)
        return json.dumps({"guidance": result})
