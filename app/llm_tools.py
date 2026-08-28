from app.tools import (
    get_payment_details,
    get_customer_history,
    analyze_failure,
    predict_recovery,
    evaluate_recovery_action
)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_payment_details",
            "description": (
                "Retrieve complete payment information "
                "for a payment ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": "The payment ID."
                    }
                },
                "required": ["payment_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_customer_history",
            "description": (
                "Retrieve the customer's historical "
                "payment success and failure information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment": {
                        "type": "object",
                        "description": "Payment record."
                    }
                },
                "required": ["payment"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "analyze_failure",
            "description": (
                "Analyze the reason a payment failed, "
                "including payment method, bank, and "
                "attempt number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment": {
                        "type": "object",
                        "description": "Payment record."
                    }
                },
                "required": ["payment"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "predict_recovery",
            "description": (
                "Use the machine learning model to "
                "predict recovery probabilities for "
                "possible recovery actions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment": {
                        "type": "object",
                        "description": "Payment record."
                    }
                },
                "required": ["payment"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "evaluate_recovery_action",
            "description": (
                "Use the deterministic recovery decision "
                "engine to select the safest and most "
                "valuable recovery action. This tool "
                "contains business guardrails and must "
                "determine the final action."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment": {
                        "type": "object",
                        "description": "Payment record."
                    }
                },
                "required": ["payment"]
            }
        }
    }
]


def execute_tool(name, arguments):

    if name == "get_payment_details":

        return get_payment_details(
            arguments["payment_id"]
        )

    if name == "get_customer_history":

        return get_customer_history(
            arguments["payment"]
        )

    if name == "analyze_failure":

        return analyze_failure(
            arguments["payment"]
        )

    if name == "predict_recovery":

        return predict_recovery(
            arguments["payment"]
        )

    if name == "evaluate_recovery_action":

        return evaluate_recovery_action(
            arguments["payment"]
        )

    return {
        "error": f"Unknown tool: {name}"
    }
