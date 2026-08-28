import json

from ollama import chat

from app.tools import (
    get_payment_details,
    get_customer_history,
    analyze_failure,
    predict_recovery,
    evaluate_recovery_action
)


MODEL = "qwen3:4b"


SYSTEM_PROMPT = """
You are an AI payment recovery agent.

Your job is to investigate failed payments and recommend
a recovery action.

You have access to tools that provide payment information,
customer history, failure analysis, ML predictions, and
a deterministic recovery decision engine.

IMPORTANT RULES:

1. Never invent payment information.
2. Use tools to obtain payment information.
3. Do not override the decision engine.
4. The decision engine contains the business rules and
   guardrails for the final recovery action.
5. Explain the reasoning behind the final recommendation.
6. Keep the final answer concise and structured.
"""


def investigate_payment(payment_id):

    payment = get_payment_details(payment_id)

    if payment is None:
        return {
            "error": f"Payment {payment_id} was not found."
        }

    history = get_customer_history(payment)

    failure = analyze_failure(payment)

    predictions = predict_recovery(payment)

    decision = evaluate_recovery_action(payment)

    prompt = f"""
Investigate the following failed payment.

PAYMENT:
{json.dumps(payment, indent=2)}

CUSTOMER HISTORY:
{json.dumps(history, indent=2)}

FAILURE ANALYSIS:
{json.dumps(failure, indent=2)}

ML RECOVERY PREDICTIONS:
{json.dumps(predictions, indent=2)}

DECISION ENGINE RESULT:
{json.dumps(decision, indent=2)}

Explain:

1. Why the payment likely failed.
2. What the ML model predicts.
3. What business constraints apply.
4. What action the decision engine recommends.
5. Why that action is appropriate.

Do not change the decision engine's recommendation.
"""

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return {
        "payment_id": payment_id,
        "decision": decision,
        "analysis": response["message"]["content"]
    }


if __name__ == "__main__":

    result = investigate_payment("PAY_000001")

    print("\n========================================")
    print("       AI PAYMENT RECOVERY AGENT")
    print("========================================")

    print(result["analysis"])

    print("\n========================================")
    print("          FINAL DECISION")
    print("========================================")

    print(
        f"Action: "
        f"{result['decision']['recommended_action']}"
    )

    print(
        f"Recovery probability: "
        f"{result['decision']['recovery_probability'] * 100:.2f}%"
    )

    print(
        f"Incremental expected value: "
        f"₹{result['decision']['incremental_expected_value']:,.2f}"
    )
