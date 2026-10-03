# TDetect - Fraud & Anomaly Investigation Copilot

An AI-assisted fraud investigation tool built on Snowflake's AI Data Cloud, for the Snowflake CoCo CLI Hackathon (GCC Edition). TDetect helps a fraud analyst move from "here's a flagged transaction" to "here's the evidence, here's what similar cases looked like, here's a recommendation" - with a human making every final decision.

> Built as a portfolio project to demonstrate Snowflake + AI product design, not a production fraud system. See limitations below.

---

## What it does

- **Risk scoring** - 5 explainable, rule-based signals (unusual amount, new device, unusual location, high transaction velocity, unusual merchant) combine into a transparent 0–100 risk score.
- **AI copilot** - ask "why was this flagged?" in plain English; answers are grounded strictly in the transaction's actual data, with the raw evidence shown alongside so nothing has to be taken on faith.
- **Natural-language queries** - ask things like "show me all critical transactions from new devices" across the whole dataset; the app converts it to SQL, shows the generated query, and runs it read-only with a safety check.
- **Similar-case lookup** - surfaces past transactions with the same signal pattern.
- **Human-in-the-loop decisions** - Confirm Fraud / Mark Legitimate / Escalate, logged to a permanent, append-only audit trail. The AI never closes a case on its own.
- **Two views** - an Analyst view for case-by-case investigation, and a Manager view with rolled-up metrics.

## Screenshots

<img width="624" height="267" alt="image" src="https://github.com/user-attachments/assets/12352754-5854-434f-bebe-2a68a88ce9c9" />
<img width="624" height="267" alt="image" src="https://github.com/user-attachments/assets/5fb424df-cda6-4acc-9094-7b9ea2728d36" />
<img width="624" height="272" alt="image" src="https://github.com/user-attachments/assets/73ee65eb-4f36-474a-87ca-179f32dd5b20" />
<img width="624" height="268" alt="image" src="https://github.com/user-attachments/assets/33700ce6-b15f-4cac-850d-2541f7ecea0c" />


## Tech stack

| Layer | Tool |
|---|---|
| Data warehouse | Snowflake (RAW → ANALYTICS → CASES schemas) |
| Risk scoring | SQL views (rule-based, no ML model) |
| AI / LLM | Snowflake Cortex (`CORTEX.COMPLETE`, `llama3.1-8b`) |
| Application | Streamlit in Snowflake |
| Data | Synthetic transaction dataset (50 customers, ~1,800 transactions) |

## Project structure

```
tdetect/
├── app/
│   └── tdetect_dashboard.py       # Streamlit app (Analyst + Manager views)
├── sql/
│   ├── 01_setup_and_cleaning.sql  # Schema, raw load, cleaning
│   ├── 02_customer_behavior.sql   # Customer baseline aggregates
│   ├── 03_anomaly_features.sql    # 5 risk signals (view)
│   ├── 04_risk_scores.sql         # Weighted scoring + risk level (view)
│   └── 05_fraud_cases.sql         # Human decision / audit trail table
├── data/
│   └── synthetic_transactions.csv
├── docs/
│   ├── PRODUCT_DEFINITION.md
│   ├── DECISION_LOG.md
│   ├── METRICS_AND_RESPONSIBLE_AI.md
│   ├── TEST_CASES.md
│   └── CASE_STUDY.md              # Full PM case study
└── README.md
```

## How to run it

1. Create a Snowflake account (a free trial works - this project used the $400 trial credit).
2. Run the SQL scripts in `sql/` in order, in a Snowsight worksheet, to set up the schema and load the data.
3. In Snowsight, go to **Apps → Streamlit App**, create a new app in the `ANALYTICS` schema, and paste in `app/tdetect_dashboard.py`.
4. Click **Run**.

## Architecture

```
Synthetic transaction data
        ↓
Snowflake (RAW → ANALYTICS → CASES)
        ↓
Risk engine (5 rule-based signals → weighted 0–100 score)
        ↓
AI layer (Snowflake Cortex - grounded explanation + NL-to-SQL)
        ↓
Streamlit app (Analyst View + Manager View)
        ↓
Human decision (Confirm Fraud / Mark Legitimate / Escalate)
        ↓
Audit trail (feeds back into future calibration)
```

## A few notable decisions

- **Rule-based scoring, not a trained ML model** - no validated fraud-labeled dataset existed; an explainable v1 was judged more honest than a misleading model trained on synthetic labels.
- **Caught and fixed a data-leakage bug (twice)** - customer "normal" baselines were briefly being computed from data that included the anomaly being evaluated, silently masking it.
- **AI-generated SQL is never trusted blindly** - every generated query is shown to the user and checked against a blocklist before running; the analyst's original question is also pre-screened for destructive language.

Full reasoning for every decision, including alternatives considered and why they were rejected, is in [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md). The full product case study - problem, users, architecture, AI design, metrics, responsible AI, and roadmap - is in [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md).

## Limitations

- This is a prototype built on synthetic data, not a production fraud system.
- Risk scoring is rule-based, not machine-learned - see the decision log for why, and the roadmap for the intended upgrade path.
- Natural-language querying is scoped to one table and SELECT-only by design, not a general-purpose database assistant.
- A few SQL queries use string interpolation for prototype simplicity; a production version would use parameterized queries throughout.

## Demo

https://youtu.be/JJ8N95TMt7o

## Author

Built by Ritika Singh for the Snowflake CoCo CLI Hackathon (GCC Edition).
