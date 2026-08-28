import pandas as pd
import joblib

from src.decision_engine import evaluate_actions


DATA_PATH = "data/payment_recovery_data.csv"
MODEL_PATH = "models/recovery_model.pkl"

model = joblib.load(MODEL_PATH)


def get_payment_details(payment_id):
    """
    Retrieve payment information using payment_id.
    """

    df = pd.read_csv(DATA_PATH)

    payment = df[
        df["payment_id"] == payment_id
    ]

    if payment.empty:
        return None

    record = payment.iloc[0]

    return {
        "payment_id": record["payment_id"],
        "amount": float(record["amount"]),
        "payment_method": record["payment_method"],
        "failure_reason": record["failure_reason"],
        "bank": record["bank"],
        "previous_successes": int(record["previous_successes"]),
        "previous_failures": int(record["previous_failures"]),
        "attempt_number": int(record["attempt_number"]),
        "customer_age_days": int(record["customer_age_days"]),
        "hour": int(record["hour"]),
        "day_of_week": int(record["day_of_week"])
    }


def get_customer_history(payment):
    """
    Extract useful customer history from a payment record.
    """

    return {
        "previous_successes": int(
            payment["previous_successes"]
        ),
        "previous_failures": int(
            payment["previous_failures"]
        ),
        "customer_age_days": int(
            payment["customer_age_days"]
        )
    }


def analyze_failure(payment):
    """
    Provide structured information about why
    the payment failed.
    """

    return {
        "failure_reason": payment["failure_reason"],
        "payment_method": payment["payment_method"],
        "bank": payment["bank"],
        "attempt_number": int(
            payment["attempt_number"]
        )
    }


def predict_recovery(payment):
    """
    Predict recovery probability for each
    possible recovery action.
    """

    actions = [
        "retry_now",
        "retry_later",
        "payment_link",
        "change_payment_method",
        "no_action"
    ]

    predictions = []

    for action in actions:

        candidate = payment.copy()

        candidate["recovery_action"] = action

        candidate_df = pd.DataFrame([candidate])

        probability = model.predict_proba(
            candidate_df
        )[0][1]

        predictions.append({
            "action": action,
            "recovery_probability": float(
                probability
            )
        })

    return predictions


def evaluate_recovery_action(payment):
    """
    Run the recovery decision engine
    for a payment.
    """

    results = evaluate_actions(payment)

    best_action = results.iloc[0]

    return {
    "recommended_action": best_action["action"],
    "recovery_probability": float(
        best_action["recovery_probability"]
    ),
    "incremental_recovery": float(
        best_action["incremental_recovery"]
    ),
    "incremental_expected_value": float(
        best_action["incremental_expected_value"]
    ),
    "baseline_probability": float(
        best_action["baseline_probability"]
    ),
    "action_cost": float(
        best_action["action_cost"]
    ),
    "decision_guardrails": best_action.get(
        "decision_guardrails",
        []
    )
}