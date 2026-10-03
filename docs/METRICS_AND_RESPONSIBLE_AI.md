# TDetect - Metrics & Responsible AI

## Metrics

**North Star metric**
Average investigation time per high-risk alert.
*(Target metric - not yet measured against a real baseline; this project has no "before AI" investigation-time data to compare against.)*

**Supporting metrics** *(prototype evaluation, based on the current synthetic dataset)*

| Metric | Current value | Note |
|---|---|---|
| Total transactions monitored | 1,822 | Synthetic dataset, 90-day window |
| Anomalies flagged | 49 | ~2.7% of all transactions |
| High-risk detection | 11 | Risk score 61-80 |
| Critical-risk detection | 2 | Risk score 81-100 |
| Copilot answer accuracy | Not yet measured | Would need a labeled question set to evaluate systematically |
| Similar-case retrieval accuracy | Not yet measured | Based on exact signal-match today, not semantic similarity |
| Analyst decision rate | 1 decision recorded so far | Will grow as the app is used |
| Copilot latency | Not yet measured | Would need repeated timed runs to report reliably |

**Honest note:** several rows above say "not yet measured" rather than a fabricated number. This is intentional - the plan explicitly warns against inventing results, and a prototype with a small synthetic dataset genuinely doesn't have enough volume for some of these to be statistically meaningful yet.

---

## Responsible AI

**Human approval required**
AI recommendations (risk scores, suggested actions) are advisory only. Every case ends with an analyst decision (Confirm Fraud / Mark Legitimate / Escalate) - the AI never blocks a transaction or closes a case on its own.

**Evidence-based responses**
The copilot is prompted to answer only from the specific transaction and customer-baseline data supplied to it, and instructed to say so explicitly if the data is insufficient, rather than inventing an answer. Every AI explanation sits next to the raw evidence (flags, ratios, customer baseline) so an analyst can verify it independently.

**Auditability**
Every analyst decision is permanently logged (transaction, risk score, recommended action, analyst decision, timestamp). Corrections are never overwritten - if a decision is changed, both the original and the correction remain visible in the audit trail.

**Privacy**
The investigation workflow only surfaces the transaction and behavioral attributes needed to explain a risk flag (amount, location, device, merchant, timing) - no unrelated customer data is exposed.

**Limitations**
- V1 uses rule-based, explainable risk scoring, not a trained supervised fraud-detection model. A production V2 would require validated historical fraud labels.
- Natural-language-to-SQL generation is scoped to a single known table and restricted to SELECT-only queries; it is not a general-purpose database assistant.
- The dataset is synthetic; real transaction volume and fraud patterns would very likely surface edge cases this design doesn't yet handle.
- Some metrics above are not yet measurable at this dataset's scale and are marked accordingly rather than estimated.
