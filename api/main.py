from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.agent import run_agent


app = FastAPI(
    title="Adaptive Payment Recovery API",
    description="AI-powered payment recovery investigation API",
    version="1.0.0"
)


class PaymentRequest(BaseModel):
    payment_id: str


@app.get("/")
def root():
    return {
        "service": "Adaptive Payment Recovery API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/recover")
def recover_payment(request: PaymentRequest):

    try:

        result = run_agent(request.payment_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        payment = result["payment"]
        customer_history = result["customer_history"]
        failure_analysis = result["failure_analysis"]
        predictions = result["ml_predictions"]
        decision = result["decision_engine"]

        return {
            "payment_id": request.payment_id,

            "payment": {
                "amount": payment["amount"],
                "payment_method": payment["payment_method"],
                "failure_reason": payment["failure_reason"],
                "bank": payment["bank"],
                "attempt_number": payment["attempt_number"],
                "hour": payment["hour"],
                "day_of_week": payment["day_of_week"]
            },

            "customer_history": customer_history,

            "failure_analysis": failure_analysis,

            "predictions": predictions,

            "decision": {
                "recommended_action": decision["recommended_action"],
                "recovery_probability": decision["recovery_probability"],
                "incremental_recovery": decision["incremental_recovery"],
                "incremental_expected_value": decision["incremental_expected_value"],
                "baseline_probability": decision.get("baseline_probability"),
                "action_cost": decision.get("action_cost"),
                "decision_guardrails": decision.get(
                    "decision_guardrails",
                    []
                )
            },

            "analysis": result["analysis"]
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )