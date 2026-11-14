
import json

from semantic_kernel.functions import kernel_function
from tools.technical_tools import (
    check_error_severity,
    search_technical_knowledge,
    validate_technical_solution
)


class TechnicalPlugin:

    @kernel_function(
        name="search_technical_knowledge",
        description="Search the technical FAQ knowledge base."
    )
    def search_knowledge(self, query: str) -> str:
        result = search_technical_knowledge(query)
        return json.dumps(result)

    @kernel_function(
        name="check_error_severity",
        description="Check whether a technical issue is potentially serious."
    )
    def check_severity(self, message: str) -> str:
        result = check_error_severity(message)
        return json.dumps(result)

    @kernel_function(
        name="validate_technical_solution",
        description="Validate a proposed technical support solution."
    )
    def validate_solution(self, solution: str) -> str:
        result = validate_technical_solution(solution)
        return json.dumps(result)
