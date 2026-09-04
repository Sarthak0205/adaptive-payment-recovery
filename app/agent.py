import json

from ollama import chat

from app.llm_tools import execute_tool


MODEL = "qwen3:4b"


SYSTEM_PROMPT = """
You are an AI payment recovery investigation agent.

You explain payment recovery decisions using ONLY the
evidence provided to you.

The Python application has already executed the required
investigation tools. Do NOT request or call any tools.

IMPORTANT RULES:

1. Never invent facts, causes, business rules, constraints,
   costs, risks, historical patterns, or operational policies.

2. The decision engine is authoritative for the final action.

3. Never override the decision engine recommendation.

4. Clearly distinguish:
   - Payment facts
   - Customer history
   - Failure analysis
   - ML predictions
   - Decision-engine recommendation

5. Never claim that a payment was actually recovered unless
   the provided evidence explicitly says it was recovered.

6. Never confuse recovery probability with incremental recovery
   or incremental expected value.

7. Never claim the recommended action has the highest raw
   recovery probability unless the ML results actually show this.

8. If retry actions were excluded by a guardrail, state the
   actual guardrail provided by the decision-engine evidence.

9. Do not invent reasons for why a guardrail exists.

10. Use INR (₹) for monetary values.

11. Preserve numerical values from the evidence accurately.

12. Round percentages to two decimal places and monetary values
    to two decimal places for readability.

FINAL RESPONSE FORMAT:

Failure:
<failure reason>

Customer:
<brief relevant customer history>

ML predictions:
<list all recovery probabilities>

Decision:
<recommended action>

Recovery probability:
<percentage>

Incremental recovery:
<percentage>

Incremental expected value:
<₹ amount>

Reason:
Explain the decision using the decision-engine evidence.

The explanation MUST:
1. Identify the highest raw ML recovery probability.
2. If that action was excluded by a guardrail, explicitly state
   that it was excluded and quote the actual guardrail evidence.
3. State the baseline/no-action recovery probability when available.
4. Explain the recommended action using incremental recovery
   and incremental expected value.
5. Mention the action cost when available.
6. Do not claim that the recommended action has the highest raw
   recovery probability if another eligible or ineligible action
   has a higher raw probability.
7. Do not invent any additional business reasoning.

For this evidence, distinguish clearly between:
- raw ML probability,
- guardrail eligibility,
- incremental recovery,
- action cost,
- incremental expected value,
- final decision.

Do not add unsupported business reasoning.
"""


def run_agent(payment_id):

    print("\n========================================")
    print("          AGENT STARTED")
    print("========================================")

    # ==================================================
    # 1. GET PAYMENT DETAILS
    # ==================================================

    payment = execute_tool(
        "get_payment_details",
        {
            "payment_id": payment_id
        }
    )

    print("\n[AGENT TOOL CALL] get_payment_details")
    print(f"Arguments: {{'payment_id': '{payment_id}'}}")
    print(
        f"[TOOL RESULT] "
        f"{json.dumps(payment, indent=2, default=str)}"
    )

    if payment is None:

        print("\nPayment not found.")

        return None

    # ==================================================
    # 2. CUSTOMER HISTORY
    # ==================================================

    customer_history = execute_tool(
        "get_customer_history",
        {
            "payment": payment
        }
    )

    print("\n[AGENT TOOL CALL] get_customer_history")
    print(
        f"Arguments: "
        f"{json.dumps({'payment': payment}, default=str)}"
    )
    print(
        f"[TOOL RESULT] "
        f"{json.dumps(customer_history, indent=2, default=str)}"
    )

    # ==================================================
    # 3. FAILURE ANALYSIS
    # ==================================================

    failure_analysis = execute_tool(
        "analyze_failure",
        {
            "payment": payment
        }
    )

    print("\n[AGENT TOOL CALL] analyze_failure")
    print(
        f"Arguments: "
        f"{json.dumps({'payment': payment}, default=str)}"
    )
    print(
        f"[TOOL RESULT] "
        f"{json.dumps(failure_analysis, indent=2, default=str)}"
    )

    # ==================================================
    # 4. ML PREDICTIONS
    # ==================================================

    predictions = execute_tool(
        "predict_recovery",
        {
            "payment": payment
        }
    )

    print("\n[AGENT TOOL CALL] predict_recovery")
    print(
        f"Arguments: "
        f"{json.dumps({'payment': payment}, default=str)}"
    )
    print(
        f"[TOOL RESULT] "
        f"{json.dumps(predictions, indent=2, default=str)}"
    )

    # ==================================================
    # 5. DECISION ENGINE
    # ==================================================

    decision = execute_tool(
        "evaluate_recovery_action",
        {
            "payment": payment
        }
    )

    print("\n[AGENT TOOL CALL] evaluate_recovery_action")
    print(
        f"Arguments: "
        f"{json.dumps({'payment': payment}, default=str)}"
    )
    print(
        f"[TOOL RESULT] "
        f"{json.dumps(decision, indent=2, default=str)}"
    )

    # ==================================================
    # 6. SEND COMPLETE EVIDENCE TO QWEN
    # ==================================================

    evidence = {
        "payment": payment,
        "customer_history": customer_history,
        "failure_analysis": failure_analysis,
        "ml_predictions": predictions,
        "decision_engine": decision
    }

    user_prompt = f"""
Investigate the payment using the evidence below.

You must explain the decision using ONLY this evidence.

Do not call tools.
Do not invent information.
Do not recalculate values.

EVIDENCE:

{json.dumps(evidence, indent=2, default=str)}

Provide the final analysis using the required format.
"""

    try:
        response = chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        final_answer = response["message"]["content"]

    except Exception:
        highest_prediction = max(
            predictions,
            key=lambda item: item["recovery_probability"]
        )

        guardrail_text = (
            "The following guardrails were applied: "
            + "; ".join(decision["decision_guardrails"])
            + ". "
            if decision["decision_guardrails"]
            else ""
        )

        final_answer = (
            f"Failure:\n"
            f"{failure_analysis['failure_reason']}\n\n"

            f"Customer:\n"
            f"previous_successes: "
            f"{customer_history['previous_successes']}, "
            f"previous_failures: "
            f"{customer_history['previous_failures']}, "
            f"customer_age_days: "
            f"{customer_history['customer_age_days']}\n\n"

            f"ML predictions:\n"
            + "\n".join(
                f"{item['action']}: "
                f"{item['recovery_probability'] * 100:.2f}%"
                for item in predictions
            )
            + "\n\n"

            f"Decision:\n"
            f"{decision['recommended_action']}\n\n"

            f"Recovery probability:\n"
            f"{decision['recovery_probability'] * 100:.2f}%\n\n"

            f"Incremental recovery:\n"
            f"{decision['incremental_recovery'] * 100:.2f}%\n\n"

            f"Incremental expected value:\n"
            f"₹{decision['incremental_expected_value']:.2f}\n\n"

            f"Reason:\n"
            f"The highest raw ML recovery probability is "
            f"{highest_prediction['recovery_probability'] * 100:.2f}% "
            f"for \"{highest_prediction['action']}\". "

            f"The decision engine recommends "
            f"\"{decision['recommended_action']}\". "

            f"{guardrail_text}"

            f"The baseline recovery probability is "
            f"{decision['baseline_probability'] * 100:.2f}%. "

            f"The incremental recovery is "
            f"{decision['incremental_recovery'] * 100:.2f}% "
            f"and the incremental expected value is "
            f"₹{decision['incremental_expected_value']:.2f}. "

            f"The action cost is "
            f"₹{decision['action_cost']:.2f}."
        )

    print("\n========================================")
    print("          FINAL ANALYSIS")
    print("========================================")

    print(final_answer)

    return {
        "payment": payment,
        "customer_history": customer_history,
        "failure_analysis": failure_analysis,
        "ml_predictions": predictions,
        "decision_engine": decision,
        "analysis": final_answer
    }


if __name__ == "__main__":

    run_agent("PAY_000001")