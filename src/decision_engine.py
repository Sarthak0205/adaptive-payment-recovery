import joblib
import pandas as pd


MODEL_PATH = "models/recovery_model.pkl"

ACTIONS = [
    "retry_now",
    "retry_later",
    "payment_link",
    "change_payment_method",
    "no_action"
]

ACTION_COSTS = {
    "retry_now": 5.00,
    "retry_later": 5.00,
    "payment_link": 1.00,
    "change_payment_method": 2.00,
    "no_action": 0.00
}

# Prototype business policy.
# This is NOT a real Razorpay threshold.
MIN_RECOVERY_PROBABILITY = 0.40


# --------------------------------------------------
# Load trained model
# --------------------------------------------------

model = joblib.load(MODEL_PATH)


# --------------------------------------------------
# Policy / Guardrails
# --------------------------------------------------

def apply_guardrails(payment, results):

    failure_reason = payment["failure_reason"]
    attempt_number = payment["attempt_number"]

    # Blocked cards should not be automatically retried.
    if failure_reason == "blocked_card":

        results = results[
            ~results["action"].isin([
                "retry_now",
                "retry_later"
            ])
        ]

    # Stop repeated automatic retries.
    if attempt_number >= 3:

        results = results[
            ~results["action"].isin([
                "retry_now",
                "retry_later"
            ])
        ]

    return results


# --------------------------------------------------
# Evaluate recovery actions
# --------------------------------------------------

def evaluate_actions(payment):

    results = []

    for action in ACTIONS:

        candidate = payment.copy()

        candidate["recovery_action"] = action

        candidate_df = pd.DataFrame([candidate])

        probability = model.predict_proba(candidate_df)[0][1]

        action_cost = ACTION_COSTS[action]

        results.append({
            "action": action,
            "recovery_probability": probability,
            "action_cost": action_cost
        })

    results = pd.DataFrame(results)

    # ----------------------------------------------
    # Baseline = probability of recovering naturally
    # ----------------------------------------------

    baseline_row = results[
        results["action"] == "no_action"
    ].iloc[0]

    baseline_probability = (
        baseline_row["recovery_probability"]
    )

    # ----------------------------------------------
    # Calculate incremental recovery and value
    # ----------------------------------------------

    results["incremental_recovery"] = (
        results["recovery_probability"]
        - baseline_probability
    )

    results["incremental_expected_value"] = (
        results["incremental_recovery"]
        * payment["amount"]
        - results["action_cost"]
    )

    # No action is the baseline, so its incremental
    # value is explicitly zero.
    results.loc[
        results["action"] == "no_action",
        "incremental_expected_value"
    ] = 0.0

    # ----------------------------------------------
    # Apply guardrails
    # ----------------------------------------------

    results = apply_guardrails(
        payment,
        results
    )

    # ----------------------------------------------
    # Remove actions below confidence threshold
    # ----------------------------------------------

    intervention_results = results[
        results["action"] != "no_action"
    ]

    intervention_results = intervention_results[
        intervention_results["recovery_probability"]
        >= MIN_RECOVERY_PROBABILITY
    ]

    # ----------------------------------------------
    # If no intervention qualifies → no action
    # ----------------------------------------------

    if intervention_results.empty:

        return results[
            results["action"] == "no_action"
        ].reset_index(drop=True)

    # ----------------------------------------------
    # Choose highest incremental value
    # ----------------------------------------------

    best = intervention_results.sort_values(
        "incremental_expected_value",
        ascending=False
    ).iloc[0]

    return pd.concat(
        [
            pd.DataFrame([best]),
            results[
                results["action"] == "no_action"
            ]
        ],
        ignore_index=True
    )


# --------------------------------------------------
# Example payment
# --------------------------------------------------

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


# --------------------------------------------------
# Run decision engine
# --------------------------------------------------

results = evaluate_actions(payment)


print("\n========== ACTION EVALUATION ==========\n")

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


print("\n========== RECOMMENDATION ==========\n")

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