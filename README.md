# Adaptive Payment Recovery

An AI-powered payment recovery decision engine that combines machine learning predictions, deterministic business guardrails, and expected-value optimization to select the best recovery action for a failed payment.

The system evaluates five possible actions:

- Retry Now
- Retry Later
- Payment Link
- Change Payment Method
- No Action

The key idea is that the system does **not** simply choose the action with the highest ML probability.

Instead:

```text
Failed Payment
      ↓
Payment + Customer Context
      ↓
ML Recovery Predictions
      ↓
Business Guardrails
      ↓
Incremental Recovery + Expected Value
      ↓
Best Eligible Action
      ↓
AI Explanation
````
#Architecture

                         FAILED PAYMENT
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Payment + Customer Data │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    ML Recovery Model    │
                 │   Logistic Regression   │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │  Recovery Probabilities │
                 │  5 candidate actions    │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   Business Guardrails   │
                 │ Retry limits / blockers │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ Expected-Value Engine   │
                 │ Recovery − cost         │
                 └────────────┬────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  FINAL DECISION  │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌─────────────────────────┐
                 │     Qwen3 4B / Ollama   │
                 │    Explanation Layer    │
                 └────────────┬────────────┘
                              │
                              ▼
                       HUMAN-READABLE
                         EXPLANATION
---

## How It Works

For each candidate recovery action, the ML model estimates:

```text
P(recovered = 1 | payment features, recovery action)
```

The `no_action` probability is used as the baseline.

### Incremental Recovery

```text
incremental_recovery
    = action_probability - baseline_probability
```

### Incremental Expected Value

```text
incremental_expected_value
    = incremental_recovery × payment_amount - action_cost
```

The decision engine selects the eligible action with the highest incremental expected value.

This means a high ML probability does **not** automatically result in that action being selected.

---

## Guardrails

The decision engine applies deterministic business constraints.

### Retry Threshold

When:

```text
attempt_number >= 3
```

`Retry Now` and `Retry Later` become ineligible.

### Blocked Card

When:

```text
failure_reason == blocked_card
```

retry actions become ineligible.

The original ML predictions remain visible, while the guardrails determine which actions can actually be selected.

---

## Machine Learning

The recovery model uses a Scikit-learn pipeline:

```text
Categorical Features
        ↓
OneHotEncoder
        ↓
Numerical Features
        ↓
StandardScaler
        ↓
Logistic Regression
```

Features include:

* Payment method
* Failure reason
* Bank
* Recovery action
* Transaction amount
* Previous successes
* Previous failures
* Attempt number
* Customer age
* Hour
* Day of week

The current dataset contains **20,000 synthetic payment transactions**.

### Current Evaluation

| Metric    |  Score |
| --------- | -----: |
| Accuracy  | 65.70% |
| Precision | 61.93% |
| Recall    | 61.93% |
| F1 Score  | 61.93% |
| ROC-AUC   | 72.41% |

These metrics are based on the synthetic dataset used by the prototype and should not be interpreted as production performance.

---

## AI Explanation

The project uses a locally hosted **Qwen3 4B** model through Ollama.

The LLM receives the structured evidence produced by the application:

* Payment details
* Customer history
* Failure context
* ML predictions
* Guardrails
* Decision-engine results
* Recovery metrics

The LLM is used only for explanation.

```text
ML Model
   ↓
Decision Engine ← Business Guardrails
   ↓
Final Decision
   ↓
LLM Explanation
```

The LLM does not make or override the final recovery decision.

---

## Example Decisions

The demo includes four representative cases:

| Payment    | Decision     | Reason                             |
| ---------- | ------------ | ---------------------------------- |
| PAY_000001 | Payment Link | Highest eligible expected value    |
| PAY_000002 | Retry Later  | Retry remains eligible             |
| PAY_000008 | Payment Link | Retry actions blocked at attempt 3 |
| PAY_000016 | No Action    | Blocked card + attempt count 4     |

One important demonstration is `PAY_000008`:

```text
Retry Later
ML probability: 41.86%
        ↓
Retry blocked by guardrail
        ↓
Payment Link
ML probability: 39.50%
        ↓
Final Decision
```

This demonstrates the difference between **prediction** and **decisioning**.

---

## Tech Stack

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

### Machine Learning

* Scikit-learn
* Pandas
* NumPy
* Joblib
* Logistic Regression

### AI

* Ollama
* Qwen3 4B

### Frontend

* React
* Vite
* CSS

### Data

* CSV
* Synthetic payment recovery dataset

---

## Project Structure

```text
adaptive-payment-recovery/
├── api/
│   └── main.py
├── app/
│   ├── agent.py
│   ├── llm_agent.py
│   ├── llm_tools.py
│   └── tools.py
├── data/
│   └── payment_recovery_data.csv
├── models/
│   └── recovery_model.pkl
├── src/
│   ├── analyze_data.py
│   ├── decision_engine.py
│   ├── generate_data.py
│   └── train_model.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── ...
├── requirements.txt
└── README.md
```

---

## Setup

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Ollama

The explanation layer requires Ollama with:

```text
qwen3:4b
```

---

## API

### Recover Payment

```http
POST /recover
```

Request:

```json
{
  "payment_id": "PAY_000008"
}
```

The response contains:

* Payment information
* Customer history
* Failure analysis
* ML predictions
* Decision-engine result
* AI explanation

Additional endpoints:

```http
GET /
GET /health
```

---

## Limitations

This is a prototype demonstrating the decision-engine architecture.

* Training data is synthetic.
* Model probabilities are not causal estimates.
* The current data source is CSV.
* The LLM requires a local Ollama installation.
* No authentication or production infrastructure is included.
* Model performance has not been validated on real payment data.

---

## Key Idea

The system separates four responsibilities:

**ML predicts.**

Estimate recovery probability for each possible action.

**Guardrails constrain.**

Remove actions that violate business rules.

**Economics decides.**

Choose the eligible action with the highest incremental expected value.

**AI explains.**

Provide a human-readable explanation of the final decision.

The result is an adaptive payment recovery system that goes beyond simply asking:

> **"Which action has the highest probability?"**

and instead asks:

> **"Which eligible action creates the greatest incremental value?"**
