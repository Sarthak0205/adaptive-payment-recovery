import numpy as np
import pandas as pd

np.random.seed(42)

N = 20000

payment_methods = ["UPI", "Card", "NetBanking", "Wallet"]
failure_reasons = [
    "gateway_error",
    "otp_failure",
    "insufficient_balance",
    "blocked_card",
    "network_error"
]
banks = ["HDFC", "ICICI", "SBI", "Axis", "Kotak"]

actions = [
    "retry_now",
    "retry_later",
    "payment_link",
    "change_payment_method",
    "no_action"
]

df = pd.DataFrame({
    "payment_id": [f"PAY_{i:06d}" for i in range(1, N + 1)],
    "amount": np.round(np.random.lognormal(mean=7.5, sigma=0.8, size=N), 2),
    "payment_method": np.random.choice(payment_methods, N),
    "failure_reason": np.random.choice(
        failure_reasons,
        N,
        p=[0.25, 0.20, 0.20, 0.15, 0.20]
    ),
    "bank": np.random.choice(banks, N),
    "previous_successes": np.random.poisson(5, N),
    "previous_failures": np.random.poisson(1.5, N),
    "attempt_number": np.random.randint(1, 5, N),
    "customer_age_days": np.random.randint(30, 1500, N),
    "hour": np.random.randint(0, 24, N),
    "day_of_week": np.random.randint(0, 7, N),
})

# Choose an action for each transaction.
df["recovery_action"] = np.random.choice(
    actions,
    N,
    p=[0.25, 0.30, 0.20, 0.15, 0.10]
)

# Base recovery probability.
probability = np.full(N, 0.45)

# Failure reason effects.
probability += np.where(
    df["failure_reason"] == "gateway_error", 0.18, 0
)

probability += np.where(
    df["failure_reason"] == "network_error", 0.12, 0
)

probability += np.where(
    df["failure_reason"] == "otp_failure", 0.05, 0
)

probability += np.where(
    df["failure_reason"] == "insufficient_balance", -0.12, 0
)

probability += np.where(
    df["failure_reason"] == "blocked_card", -0.30, 0
)

# Customer history.
probability += df["previous_successes"] * 0.025
probability -= df["previous_failures"] * 0.04

# More attempts generally reduce recovery likelihood.
probability -= (df["attempt_number"] - 1) * 0.08

# Action effects.
probability += np.where(
    df["recovery_action"] == "retry_later", 0.10, 0
)

probability += np.where(
    df["recovery_action"] == "payment_link", 0.07, 0
)

probability += np.where(
    df["recovery_action"] == "change_payment_method", 0.05, 0
)

probability += np.where(
    df["recovery_action"] == "retry_now", 0.02, 0
)

probability += np.where(
    df["recovery_action"] == "no_action", -0.15, 0
)

# Keep probabilities realistic.
probability = np.clip(probability, 0.02, 0.95)

# Generate recovery outcome.
df["recovered"] = (
    np.random.random(N) < probability
).astype(int)

# Amount recovered is the full transaction amount if successful.
df["recovered_amount"] = np.where(
    df["recovered"] == 1,
    df["amount"],
    0
)

# Save dataset.
output_path = "data/payment_recovery_data.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df):,} transactions.")
print(f"Saved to: {output_path}")
print("\nRecovery rate:")
print(f"{df['recovered'].mean() * 100:.2f}%")

print("\nSample:")
print(df.head())