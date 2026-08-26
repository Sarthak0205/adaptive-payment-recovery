import pandas as pd

df = pd.read_csv("data/payment_recovery_data.csv")

print("Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nOverall recovery rate:")
print(f"{df['recovered'].mean() * 100:.2f}%")

print("\nRecovery by failure reason:")
print(
    df.groupby("failure_reason")["recovered"]
    .mean()
    .sort_values(ascending=False)
    .mul(100)
    .round(2)
)

print("\nRecovery by action:")
print(
    df.groupby("recovery_action")["recovered"]
    .mean()
    .sort_values(ascending=False)
    .mul(100)
    .round(2)
)

print("\nRecovery by attempt number:")
print(
    df.groupby("attempt_number")["recovered"]
    .mean()
    .mul(100)
    .round(2)
)

print("\nRecovery by payment method:")
print(
    df.groupby("payment_method")["recovered"]
    .mean()
    .mul(100)
    .round(2)
)

print("\nAverage transaction amount:")
print(f"₹{df['amount'].mean():,.2f}")

print("\nTotal at-risk revenue:")
print(f"₹{df['amount'].sum():,.2f}")

print("\nTotal recovered revenue:")
print(f"₹{df['recovered_amount'].sum():,.2f}")