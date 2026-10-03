# TDetect — Fraud & Anomaly Investigation Copilot
### A PM case study

---

## 1. Problem

Fraud analysts receive large numbers of transaction alerts and must manually investigate transaction history, customer behavior, device information, and other signals before deciding whether an alert requires action. Detecting an anomaly is only the first problem — the analyst still has to understand *why* it was flagged and decide what to do about it, often under time pressure and across dozens of cases a day.

## 2. Users

**Primary: Fraud/Risk Analyst.** Investigates individual flagged transactions, needs fast, evidence-backed answers to "why was this flagged," and makes the final call on each case.

**Secondary: Risk Manager.** Doesn't investigate individual cases; needs a rolled-up view of volume, top risk signals, and where problems are concentrated, to spot systemic issues and allocate analyst attention.

## 3. User pain points

- Investigating a single alert means manually cross-referencing transaction history, device logs, and location data across multiple systems.
- Explaining *why* something was flagged to a colleague or auditor takes real effort if the reasoning isn't already written down.
- Without a record of past similar cases, every alert gets investigated from scratch, even if an identical pattern was resolved last week.
- Decisions made under time pressure are easy to lose track of — without an audit trail, corrections and second-guesses aren't visible later.

## 4. Product hypothesis

If an analyst can see a transparent risk score, ask a grounded AI copilot "why" in plain English, and see similar past cases — all in one place — investigation time per alert drops, without removing the human from the final decision.

## 5. User journey

Select suspicious transaction → understand why it was flagged → investigate the evidence → compare with historical similar cases → decide → record the decision.

In the app, this maps to: Overview dashboard → Investigation screen (risk score + evidence) → Ask the copilot → Have we seen this before? → Recommended action → Analyst decision (Confirm Fraud / Mark Legitimate / Escalate) → logged to the audit trail.

## 6. MVP — why these features, and not others

The build was deliberately scoped to these seven core pieces, in this order, because each one only makes sense once the previous one exists:

1. **Rule-based risk scoring** (not a trained ML classifier) — chosen because no validated, real fraud-labeled dataset existed to train a classifier on; a rule-based score is transparent and defensible without one.
2. **Two-persona dashboard** (Analyst + Manager) — because the same data serves two different jobs: investigating one case vs. spotting systemic patterns.
3. **Grounded AI copilot** — explains flagged transactions in plain English, but is explicitly instructed to use only the supplied data and to say so if it can't answer, rather than invent evidence.
4. **Natural-language-to-SQL** — lets an analyst ask ad-hoc questions across all transactions without knowing SQL, scoped to SELECT-only queries with a safety check before execution.
5. **Similar-case retrieval** — surfaces other transactions matching the same signal combination, so patterns aren't investigated from scratch every time.
6. **Rule-based recommendation engine** — deliberately *not* AI-generated, to keep the one piece that suggests an action fully predictable and auditable.
7. **Human-in-the-loop decision + permanent audit trail** — the AI never blocks a transaction or closes a case; every analyst decision is logged, and corrections are preserved rather than overwritten.

What was deliberately left out of v1: a trained ML fraud classifier, real-time streaming ingestion, and a general-purpose (non-scoped) natural-language database assistant — see Roadmap.

## 7. Architecture

```
Synthetic transaction data
        ↓
Snowflake (RAW → ANALYTICS → CASES schemas)
        ↓
Risk engine (5 rule-based signals → weighted 0–100 score)
        ↓
AI layer (Snowflake Cortex — grounded explanation + NL-to-SQL)
        ↓
Streamlit application (Analyst View + Manager View)
        ↓
Human decision (Confirm Fraud / Mark Legitimate / Escalate)
        ↓
Audit trail (feeds back into future risk-engine calibration)
```

Data flows one way through detection and scoring, then the AI layer sits *alongside* the data (reading from it, never writing to it) to explain and answer questions, and every human decision writes into a separate, append-only case log — kept deliberately separate from the transaction data itself so the two schemas serve different purposes: `ANALYTICS` is the system's read side, `CASES` is the human decision record.

## 8. AI design

**Grounding.** The copilot's system prompt explicitly instructs it to use only the transaction and customer-baseline data supplied in the prompt, and to say so if the data is insufficient — verified in testing to produce no hallucinated evidence.

**Prompting.** Two distinct prompts serve two distinct jobs: one explains a single transaction using its full context (amount, ratio, location, baseline comparisons, all five signal flags); the other converts a natural-language question into SQL against a single known table schema, with the schema description including domain-specific thresholds (e.g., "velocity ≥ 4 is HIGH") so the model doesn't have to guess business rules.

**Natural-language queries.** Scoped deliberately to one table and SELECT-only, rather than attempting a general text-to-SQL system — a smaller, more reliable scope beats a fragile, ambitious one.

**Similar-case retrieval.** Matches on exact signal-flag combination today (not semantic/vector similarity) — simple, explainable, and sufficient at this dataset's scale; a natural v2 upgrade path exists (see Roadmap).

**Guardrails.** Two layers: generated SQL is checked against a blocklist (DROP/DELETE/UPDATE/etc.) before execution, and the analyst's original question is also pre-screened for destructive-sounding language, so an unsafe request is caught and explained *before* even reaching the AI — closing a gap found in testing where the model would silently drop a destructive instruction without telling the analyst.

## 9. Metrics

**North Star:** Average investigation time per high-risk alert *(target metric — no real "before AI" baseline exists to compare against yet)*.

**Supporting metrics** *(prototype evaluation on the current synthetic dataset)*: 1,822 transactions monitored, 49 anomalies flagged (~2.7%), 11 High-risk, 2 Critical-risk. Copilot answer accuracy, similar-case retrieval accuracy, and copilot latency are not yet formally measured — the dataset's current scale isn't large enough for these to be statistically meaningful, and they're marked as such rather than estimated.

## 10. Responsible AI

- **Human approval required** — every AI output (score, explanation, recommendation) is advisory; the analyst makes the final call.
- **Evidence-based responses** — the copilot's explanation always sits next to the raw evidence (flags, ratios, baselines), so it can be independently verified, not just trusted.
- **Auditability** — every decision is permanently logged; corrections are preserved, never overwritten.
- **Privacy** — only the transaction and behavioral attributes needed to explain a risk flag are surfaced; no unrelated customer data.
- **Limitations** — stated plainly rather than glossed over (see below).

## 11. Limitations

- V1 risk scoring is rule-based and explainable, not a trained ML model — a real production version would need validated historical fraud labels to train and evaluate one properly.
- The natural-language-to-SQL feature is scoped to one table and SELECT-only; it is not a general-purpose database assistant.
- Similar-case matching is exact-flag-match today, not semantic similarity — a v2 could use embeddings for fuzzier pattern matching.
- The dataset is synthetic; real transaction volume and fraud patterns would likely surface edge cases this design doesn't yet handle.
- Some metrics (copilot accuracy, latency) aren't yet measurable at this dataset's scale, and are labeled "not yet measured" rather than estimated or fabricated.
- SQL string interpolation is used in a few places for simplicity in this prototype; a production version would use parameterized queries throughout.

## 12. Roadmap

**V1 (built):** rule-based risk scoring, grounded AI copilot, scoped NL-to-SQL, exact-match similar cases, human-in-the-loop decisions with a permanent audit trail, two-persona dashboard.

**V2:** trained ML fraud-scoring model (once real labeled data exists) sitting alongside the explainable rule-based layer, not replacing it; semantic/embedding-based similar-case retrieval; analyst-decision feedback loop feeding back into risk-engine calibration.

**V3:** real-time streaming ingestion in place of batch-loaded historical data; expanded natural-language querying scope; alerting/notification layer for the Manager view.

---

## Key decisions (selected from the full decision log)

- **Rule-based scoring over ML classifier** — no validated fraud labels existed; an explainable v1 with a stated ML upgrade path was judged more honest and more useful in an interview than a misleading toy model trained on synthetic labels.
- **Synthetic dataset over a real public fraud dataset** — real datasets (Kaggle credit card, PaySim) either anonymize features into unusable PCA components or lack the device/location fields this product's investigation UI depends on.
- **Engineered multi-signal "critical" transactions** — the organically-generated anomalies only ever triggered 1-2 signals at once, capping every score below the Critical threshold; a demo needs to show the system's full scoring range, not just what randomness happened to produce.
- **Customer baselines exclude anomalous transactions** — including them caused real data leakage (a transaction's own device/amount counted into its own "normal" baseline), caught and fixed twice across two different data-loading paths.
- **Recommendation engine is rule-based, not AI-generated** — keeping the one feature that suggests an action fully predictable and auditable, consistent with the project's transparency principle throughout.
- **Pre-screening the analyst's question for destructive language**, not just the generated SQL — testing revealed the model would silently drop a "delete" instruction without telling the analyst; catching it before the AI call closes that transparency gap.

*(Full entry-by-entry log, with alternatives considered and rejection reasons, lives in DECISION_LOG.md.)*
