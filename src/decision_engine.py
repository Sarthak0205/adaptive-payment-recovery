import joblib
import pandas as pd


# ============================================================
# Configuration
# ============================================================

MODEL_PATH = "models/recovery_model.pkl"

ACTIONS = [
    "retry_now",
    "retry_later",
    "payment_link",
    "change_payment_method",
    "no_action"
]

ACTION_COSTS = {
    "retry_now": 2.0,
    "retry_later": 5.0,
    "payment_link": 1.0,
    "change_payment_method": 3.0,
    "no_action": 0.0
}

MIN_RECOVERY_PROBABILITY = 0.30


# ============================================================
# Load model
# ============================================================

model = joblib.load(MODEL_PATH)


# ============================================================
# Guardrails
# ============================================================

def apply_guardrails(payment, results):
    """
    Mark retry actions as ineligible when decision-engine
    guardrails are triggered.

    The original ML probabilities are preserved.
    """

    results = results.copy()

    results["eligible"] = True

    # --------------------------------------------------------
    # Guardrail 1:
    # Block retry actions after 3 attempts
    # --------------------------------------------------------

    if payment["attempt_number"] >= 3:

        results.loc[
            results["action"].isin(
                ["retry_now", "retry_later"]
            ),
            "eligible"
        ] = False

    # --------------------------------------------------------
    # Guardrail 2:
    # Block retry actions for blocked cards
    # --------------------------------------------------------

    if payment["failure_reason"] == "blocked_card":

        results.loc[
            results["action"].isin(
                ["retry_now", "retry_later"]
            ),
            "eligible"
        ] = False

    return results


# ============================================================
# Evaluate actions
# ============================================================

def evaluate_actions(payment):
    """
    Evaluate all possible recovery actions.

    Returns:
        DataFrame containing:
        - raw ML probability
        - baseline probability
        - incremental recovery
        - incremental expected value
        - eligibility
        - guardrail evidence
    """

    results = []

    # --------------------------------------------------------
    # Generate prediction for every action
    # --------------------------------------------------------

    for action in ACTIONS:

        candidate = payment.copy()

        # IMPORTANT:
        # The trained model expects this feature.
        candidate["recovery_action"] = action

        candidate_df = pd.DataFrame([candidate])

        probability = model.predict_proba(
            candidate_df
        )[0][1]

        results.append({
            "action": action,
            "recovery_probability": float(probability),
            "action_cost": float(
                ACTION_COSTS[action]
            )
        })

    results = pd.DataFrame(results)

    # --------------------------------------------------------
    # Baseline = no_action probability
    # --------------------------------------------------------

    baseline_rows = results[
        results["action"] == "no_action"
    ]

    if baseline_rows.empty:
        raise RuntimeError(
            "Decision engine requires a no_action baseline."
        )

    baseline_probability = float(
        baseline_rows.iloc[0]["recovery_probability"]
    )

    # --------------------------------------------------------
    # Incremental recovery
    # --------------------------------------------------------

    results["incremental_recovery"] = (
        results["recovery_probability"]
        - baseline_probability
    )

    # --------------------------------------------------------
    # Incremental expected value
    # --------------------------------------------------------

    results["incremental_expected_value"] = (
        results["incremental_recovery"]
        * float(payment["amount"])
        - results["action_cost"]
    )

    # No action is the baseline.
    results.loc[
        results["action"] == "no_action",
        "incremental_recovery"
    ] = 0.0

    results.loc[
        results["action"] == "no_action",
        "incremental_expected_value"
    ] = 0.0

    # --------------------------------------------------------
    # Apply guardrails
    # --------------------------------------------------------

    results = apply_guardrails(
        payment,
        results
    )

    # --------------------------------------------------------
    # Decision evidence
    # --------------------------------------------------------

    guardrails = []

    if payment["failure_reason"] == "blocked_card":

        guardrails.append(
            "retry actions blocked because "
            "failure_reason is blocked_card"
        )

    if payment["attempt_number"] >= 3:

        guardrails.append(
            "retry actions blocked because "
            f"attempt_number is "
            f"{payment['attempt_number']} (>= 3)"
        )

    # --------------------------------------------------------
    # Eligible intervention actions
    # --------------------------------------------------------

    intervention_results = results[
        results["action"] != "no_action"
    ].copy()

    # Apply confidence threshold
    intervention_results = intervention_results[
        intervention_results["recovery_probability"]
        >= MIN_RECOVERY_PROBABILITY
    ]

    # Apply guardrails
    intervention_results = intervention_results[
        intervention_results["eligible"]
    ]

    # --------------------------------------------------------
    # No eligible intervention
    # --------------------------------------------------------

    if intervention_results.empty:

        best = results[
            results["action"] == "no_action"
        ].iloc[0].copy()

        best["baseline_probability"] = (
            baseline_probability
        )

        best["decision_guardrails"] = guardrails

        best["action_cost"] = 0.0

        return pd.DataFrame(
            [best]
        )

    # --------------------------------------------------------
    # Select action by incremental expected value
    # --------------------------------------------------------

    best = intervention_results.sort_values(
        "incremental_expected_value",
        ascending=False
    ).iloc[0].copy()

    # --------------------------------------------------------
    # Attach decision evidence
    # --------------------------------------------------------

    best["baseline_probability"] = (
        baseline_probability
    )

    best["decision_guardrails"] = guardrails

    best["action_cost"] = float(
        ACTION_COSTS[best["action"]]
    )

    # --------------------------------------------------------
    # Return recommendation + baseline
    # --------------------------------------------------------

    no_action = results[
        results["action"] == "no_action"
    ].iloc[0].copy()

    no_action["baseline_probability"] = (
        baseline_probability
    )

    no_action["decision_guardrails"] = guardrails

    no_action["action_cost"] = 0.0

    return pd.DataFrame(
        [
            best,
            no_action
        ]
    ).reset_index(drop=True)


# ============================================================
# Decision explanation
# ============================================================

def get_decision_explanation(payment):

    results = evaluate_actions(payment)

    best = results.iloc[0]

    explanation = {
        "recommended_action": str(
            best["action"]
        ),

        "recovery_probability": round(
            float(best["recovery_probability"]),
            4
        ),

        "incremental_recovery": round(
            float(best["incremental_recovery"]),
            4
        ),

        "incremental_expected_value": round(
            float(best["incremental_expected_value"]),
            2
        ),

        "baseline_probability": round(
            float(best["baseline_probability"]),
            4
        ),

        "attempt_number": int(
            payment["attempt_number"]
        ),

        "failure_reason": str(
            payment["failure_reason"]
        ),

        "action_cost": round(
            float(best["action_cost"]),
            2
        ),

        "decision_guardrails": (
            best["decision_guardrails"]
            if isinstance(
                best["decision_guardrails"],
                list
            )
            else []
        )
    }

    return explanation


# ============================================================
# Manual test
# ============================================================

if __name__ == "__main__":

    payment = {
        "amount": 500,
        "payment_method": "Card",
        "failure_reason": "blocked_card",
        "bank": "HDFC",
        "previous_successes": 0,
        "previous_failures": 5,
        "attempt_number": 4,
        "customer_age_days": 10,
        "hour": 3,
        "day_of_week": 2
    }

    results = evaluate_actions(payment)

    print(
        "\n========================================"
    )
    print(
        "          ACTION EVALUATION"
    )
    print(
        "========================================\n"
    )

    for _, row in results.iterrows():

        print(
            f"{row['action']:25s} "
            f"Recovery: "
            f"{row['recovery_probability'] * 100:6.2f}% | "
            f"Incremental: "
            f"{row['incremental_recovery'] * 100:6.2f}% | "
            f"Cost: "
            f"₹{row['action_cost']:6.2f} | "
            f"Incremental Value: "
            f"₹{row['incremental_expected_value']:,.2f}"
        )

    best_action = results.iloc[0]

    print(
        "\n========================================"
    )
    print(
        "          RECOMMENDATION"
    )
    print(
        "========================================\n"
    )

    print(
        f"Recommended action: "
        f"{best_action['action']}"
    )

    print(
        f"Recovery probability: "
        f"{best_action['recovery_probability'] * 100:.2f}%"
    )

    print(
        f"Incremental recovery: "
        f"{best_action['incremental_recovery'] * 100:.2f}%"
    )

    print(
        f"Incremental expected value: "
        f"₹{best_action['incremental_expected_value']:,.2f}"
    )

    print(
        f"Baseline probability: "
        f"{best_action['baseline_probability'] * 100:.2f}%"
    )

    print(
        f"Guardrails: "
        f"{best_action['decision_guardrails']}"
    )