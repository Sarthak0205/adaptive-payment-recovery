import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)

# --------------------------------------------------
# 1. Load data
# --------------------------------------------------

df = pd.read_csv("data/payment_recovery_data.csv")

# --------------------------------------------------
# 2. Define features and target
# --------------------------------------------------

features = [
    "amount",
    "payment_method",
    "failure_reason",
    "bank",
    "previous_successes",
    "previous_failures",
    "attempt_number",
    "customer_age_days",
    "hour",
    "day_of_week",
    "recovery_action"
]

X = df[features]
y = df["recovered"]

# --------------------------------------------------
# 3. Identify categorical and numerical features
# --------------------------------------------------

categorical_features = [
    "payment_method",
    "failure_reason",
    "bank",
    "recovery_action"
]

numerical_features = [
    "amount",
    "previous_successes",
    "previous_failures",
    "attempt_number",
    "customer_age_days",
    "hour",
    "day_of_week"
]

# --------------------------------------------------
# 4. Preprocessing
# --------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "numerical",
            StandardScaler(),
            numerical_features
        )
    ]
)

# --------------------------------------------------
# 5. Create ML pipeline
# --------------------------------------------------

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000))
    ]
)

# --------------------------------------------------
# 6. Train/test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Training samples: {len(X_train):,}")
print(f"Testing samples:  {len(X_test):,}")

# --------------------------------------------------
# 7. Train
# --------------------------------------------------

model.fit(X_train, y_train)

#---------------------------------------------------
# SAVE TRAINED MODEL 
#---------------------------------------------------

joblib.dump(model, "models/recovery_model.pkl")

print("\nModel saved to: models/recovery_model.pkl")

# --------------------------------------------------
# 8. Predictions
# --------------------------------------------------

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]

# --------------------------------------------------
# 9. Evaluation
# --------------------------------------------------

print("\n========== MODEL RESULTS ==========")

print(
    f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}"
)

print(
    f"Precision: {precision_score(y_test, y_pred):.4f}"
)

print(
    f"Recall:    {recall_score(y_test, y_pred):.4f}"
)

print(
    f"F1 Score:  {f1_score(y_test, y_pred):.4f}"
)

print(
    f"ROC-AUC:   {roc_auc_score(y_test, y_probability):.4f}"
)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))