import { useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  CreditCard,
  Search,
  ShieldAlert,
  TrendingUp,
  UserRound,
} from "lucide-react";
import "./App.css";

const API_URL = "/api";

function App() {
  const [paymentId, setPaymentId] = useState("PAY_000001");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzePayment = async (id = paymentId) => {
    const targetId = id.trim();

    if (!targetId) return;

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch(`${API_URL}/recover`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          payment_id: targetId,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Unable to analyze payment");
      }

      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };



  const payment = data?.payment;
  const customer = data?.customer_history;
  const predictions = data?.predictions || [];
  const decision = data?.decision;
  const analysis = data?.analysis;

  const recommendedAction = decision?.recommended_action
    ?.replaceAll("_", " ")
    .toUpperCase();
  const demoPayments = [
    {
      id: "PAY_000001",
      label: "Gateway Error",
      action: "Payment Link",
    },
    {
      id: "PAY_000002",
      label: "Network Error",
      action: "Retry Later",
    },
    {
      id: "PAY_000008",
      label: "3rd Attempt",
      action: "Payment Link",
    },
    {
      id: "PAY_000016",
      label: "Blocked Card",
      action: "No Action",
    },
  ];
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={20} />
          </div>

          <div>
            <div className="brand-name">Adaptive Recovery</div>
            <div className="brand-subtitle">
              AI Payment Decision Engine
            </div>
          </div>
        </div>

        <div className="api-status">
          <span className="status-dot" />
          API ONLINE
        </div>
      </header>

      <main className="dashboard">
        <section className="hero">
          <div>
            <p className="eyebrow">PAYMENT INVESTIGATION</p>
            <h1>Recovery Intelligence</h1>
            <p className="hero-description">
              Investigate failed payments and understand the
              recovery action selected by the decision engine.
            </p>
          </div>
        </section>

        <section className="search-panel">
          <div className="search-label">
            <Search size={16} />
            Payment ID
          </div>

          <div className="search-row">
            <input
              value={paymentId}
              onChange={(e) => setPaymentId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  analyzePayment();
                }
              }}
              placeholder="e.g. PAY_000001"
            />

            <button
              onClick={analyzePayment}
              disabled={loading}
            >
              {loading ? (
                "ANALYZING..."
              ) : (
                <>
                  ANALYZE
                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </div>

          {error && (
            <div className="error-message">
              <AlertTriangle size={17} />
              {error}
            </div>
          )}
        </section>

        <div className="demo-panel">
          <div className="demo-header">
            <div>
              <p className="card-eyebrow">DEMO CASES</p>
              <h2>Decision Engine Scenarios</h2>
            </div>
          </div>

          <div className="demo-grid">
            {demoPayments.map((payment) => (
              <button
                key={payment.id}
                className="demo-case"
                onClick={() => {
                  setPaymentId(payment.id);
                  analyzePayment(payment.id);
                }}
                disabled={loading}
              >
                <div>
                  <strong>{payment.id}</strong>
                  <span>{payment.label}</span>
                </div>

                <span className="demo-action">
                  {payment.action}
                </span>
              </button>
            ))}
          </div>
        </div>

        {!data && !loading && !error && (
          <section className="empty-state">
            <Brain size={42} />
            <h2>Ready for investigation</h2>
            <p>
              Enter a payment ID above to run the recovery
              analysis.
            </p>
          </section>
        )}

        {loading && (
          <section className="empty-state">
            <div className="loader" />
            <h2>Running investigation</h2>
            <p>
              Executing payment analysis, ML prediction and
              decision engine evaluation...
            </p>
          </section>
        )}

        {data && !loading && (
          <>
            <section className="grid-two">
              <div className="card payment-card">
                <div className="card-header">
                  <div>
                    <p className="card-eyebrow">PAYMENT</p>
                    <h2>{data.payment_id}</h2>
                  </div>

                  <CreditCard size={24} />
                </div>

                <div className="amount">
                  ₹{Number(payment.amount).toLocaleString("en-IN", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </div>

                <div className="detail-grid">
                  <Detail
                    label="Payment Method"
                    value={payment.payment_method}
                  />
                  <Detail
                    label="Bank"
                    value={payment.bank}
                  />
                  <Detail
                    label="Failure"
                    value={payment.failure_reason}
                  />
                  <Detail
                    label="Attempt"
                    value={payment.attempt_number}
                  />
                </div>
              </div>

              <div className="card decision-card">
                <div className="card-header">
                  <div>
                    <p className="card-eyebrow">DECISION ENGINE</p>
                    <h2>{recommendedAction}</h2>
                  </div>

                  <CheckCircle2 size={26} />
                </div>

                <div className="decision-main">
                  <div>
                    <span>Recovery Probability</span>
                    <strong>
                      {formatPercent(
                        decision.recovery_probability
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Incremental Recovery</span>
                    <strong>
                      {formatPercent(
                        decision.incremental_recovery
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Expected Value</span>
                    <strong>
                      ₹
                      {Number(
                        decision.incremental_expected_value
                      ).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </strong>
                  </div>
                </div>

                <div className="decision-footer">
                  <span>Action cost</span>
                  <strong>
                    ₹
                    {Number(decision.action_cost).toFixed(2)}
                  </strong>
                </div>
              </div>
            </section>

            <section className="card">
              <div className="section-heading">
                <div>
                  <p className="card-eyebrow">MACHINE LEARNING</p>
                  <h2>Recovery Predictions</h2>
                </div>

                <Brain size={24} />
              </div>

              <div className="prediction-list">
                {predictions.map((item) => {
                  const percentage =
                    item.recovery_probability * 100;

                  const isRecommended =
                    item.action ===
                    decision.recommended_action;

                  return (
                    <div
                      className={`prediction ${isRecommended
                        ? "recommended"
                        : ""
                        }`}
                      key={item.action}
                    >
                      <div className="prediction-top">
                        <span>
                          {item.action.replaceAll("_", " ")}
                        </span>

                        <strong>
                          {percentage.toFixed(2)}%
                        </strong>
                      </div>

                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${percentage}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="grid-two">
              <div className="card">
                <div className="section-heading">
                  <div>
                    <p className="card-eyebrow">
                      CUSTOMER HISTORY
                    </p>
                    <h2>Customer Profile</h2>
                  </div>

                  <UserRound size={23} />
                </div>

                <div className="history-grid">
                  <Metric
                    label="Previous Successes"
                    value={customer.previous_successes}
                  />
                  <Metric
                    label="Previous Failures"
                    value={customer.previous_failures}
                  />
                  <Metric
                    label="Account Age"
                    value={`${customer.customer_age_days} days`}
                  />
                </div>
              </div>

              <div className="card">
                <div className="section-heading">
                  <div>
                    <p className="card-eyebrow">
                      FAILURE ANALYSIS
                    </p>
                    <h2>Failure Context</h2>
                  </div>

                  <ShieldAlert size={23} />
                </div>

                <div className="failure-list">
                  <Detail
                    label="Failure Reason"
                    value={data.failure_analysis.failure_reason}
                  />
                  <Detail
                    label="Payment Method"
                    value={data.failure_analysis.payment_method}
                  />
                  <Detail
                    label="Bank"
                    value={data.failure_analysis.bank}
                  />
                  <Detail
                    label="Attempt Number"
                    value={data.failure_analysis.attempt_number}
                  />
                </div>
              </div>
            </section>

            {decision.decision_guardrails?.length > 0 && (
              <section className="card guardrail-card">
                <div className="section-heading">
                  <div>
                    <p className="card-eyebrow">GUARDRAILS</p>
                    <h2>Decision Constraints</h2>
                  </div>

                  <ShieldAlert size={24} />
                </div>

                {decision.decision_guardrails.map(
                  (guardrail) => (
                    <div
                      className="guardrail"
                      key={guardrail}
                    >
                      <AlertTriangle size={18} />
                      <span>{guardrail}</span>
                    </div>
                  )
                )}
              </section>
            )}

            <section className="card analysis-card">
              <div className="section-heading">
                <div>
                  <p className="card-eyebrow">AI EXPLANATION</p>
                  <h2>Decision Analysis</h2>
                </div>

                <TrendingUp size={24} />
              </div>

              <pre>{analysis}</pre>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div className="detail">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(2)}%`;
}

export default App;
