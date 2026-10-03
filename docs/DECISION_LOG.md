# TDetect - PM Decision Log

Every meaningful decision made during the build, in chronological order. Each entry follows: Decision → Why → Alternative considered → Why rejected → Future direction. These are the kind of specifics that turn "I built a fraud detection app" into "I considered X, rejected it because Y, and designed for Z" in an interview.

---

### 1. Product naming
**Decision:** Initially named the product SentinelIQ (later renamed to TDetect - see entry 20).
**Why:** Short, easy to say in an interview, and reads as an established enterprise product name rather than a generic feature description.
**Alternative considered:** RiskLens AI, and several other candidates considered later in the process.
**Why rejected:** RiskLens AI sounded more like a feature description than a product name.
**Future:** N/A - see entry 20 for the final naming decision.

---

### 2. Rule-based risk scoring instead of a trained ML model
**Decision:** Built the core risk engine as transparent, rule-based/statistical scoring (5 weighted signals, 0–100 score) rather than a trained supervised fraud classifier.
**Why:** No validated, real historical fraud-labeled dataset existed - only synthetic data. Training a classifier on synthetic or limited labels would produce a misleading toy model that looks more sophisticated than it actually is.
**Alternative considered:** A supervised machine learning classification model.
**Why rejected:** Would create false confidence in accuracy that isn't real, and is harder to explain to an analyst asking "why was this flagged?" - a rule-based score is fully transparent by construction.
**Future:** A production V2 could train and validate an ML model once real historical fraud outcomes are available, with the rule-based layer kept as an explainable fallback/baseline rather than replaced outright.

---

### 3. Synthetic dataset instead of a real public fraud dataset
**Decision:** Generated a synthetic transaction dataset (50 customers, ~1,800 transactions) instead of using a real public dataset like Kaggle's Credit Card Fraud dataset or PaySim.
**Why:** Real public datasets either anonymize their features into unusable PCA components (no interpretable fields) or lack the device/location/merchant fields this product's investigation UI and risk signals depend on.
**Alternative considered:** Kaggle Credit Card Fraud dataset, PaySim.
**Why rejected:** No interpretable device/location signals to power the "why was this flagged" explanation, which is the core of the product.
**Future:** A production version would use real transaction data with proper device/location instrumentation, likely paired with an enriched fraud dataset (e.g., IEEE-CIS style) for signal validation.

---

### 4. Skipped simulating messy/dirty data
**Decision:** Generated the synthetic dataset clean on purpose, rather than deliberately injecting missing values, duplicates, or malformed records.
**Why:** Prioritized time on the risk engine and AI layer, which are the parts recruiters and judges actually evaluate, over building a realistic-but-time-consuming data-quality problem.
**Alternative considered:** Deliberately injecting messy data to demonstrate cleaning logic.
**Why rejected:** Would cost build time without adding to the product story - the cleaning pipeline still exists and runs correctly, it just has nothing to catch in this dataset.
**Future:** A production system would ingest genuinely messy transaction feeds, and this same cleaning layer would need to handle real edge cases (partial records, schema drift, late-arriving data).

---

### 5. Excluded anomalous transactions from customer baseline calculations
**Decision:** The `CUSTOMER_BEHAVIOR` table (average amount, common location, known devices) is calculated only from non-anomalous transactions.
**Why:** Including anomalous transactions in the baseline caused real data leakage - a transaction's own device or amount would get counted into its own "normal" baseline, silently masking the exact anomaly it was supposed to trigger. This was caught through testing (the device-anomaly signal wasn't firing) and fixed.
**Alternative considered:** Computing the baseline from all historical transactions, anomalies included.
**Why rejected:** Any anomaly present at baseline-computation time becomes invisible to its own detection logic - the exact failure mode that makes fraud baselines unreliable in production if not handled carefully.
**Future:** A production system would compute baselines from a rolling window strictly prior to each transaction being scored, not a static all-time aggregate, to avoid this leakage entirely even for genuinely new anomalies.

---

### 6. Boolean literal comparison instead of string comparison for the anomaly flag
**Decision:** Replaced `is_synthetic_anomaly = 'no'` (a string comparison) with `is_synthetic_anomaly = FALSE` (a boolean literal) in the baseline query, and manually corrected affected rows via `UPDATE`.
**Why:** A second CSV load appended into an existing table caused Snowflake to coerce the `"yes"/"no"` string values into the BOOLEAN column differently than the first load did, silently reintroducing the same data-leakage bug (entry 5) in a new form.
**Alternative considered:** Re-uploading the whole file as a fresh table load instead of appending.
**Why rejected:** Slower, and doesn't fix the underlying fragility - a boolean-literal comparison is more robust regardless of how future data gets loaded.
**Future:** In a production pipeline, column types and value encodings would be enforced at ingestion (a defined schema/contract), not inferred per-load.

---

### 7. Engineered multi-signal transactions to guarantee a full risk-score range
**Decision:** Deliberately constructed a small batch of transactions that stack all 4 numeric signals simultaneously (amount + new device + unusual location + high velocity), rather than relying on organically random anomaly generation.
**Why:** The initial random anomaly generation only ever triggered 1–2 signals per transaction, capping every risk score below the Critical threshold (81+) - a demo needs to show the full range the scoring system is capable of, including what a genuinely severe case looks like.
**Alternative considered:** Lowering the Critical threshold so existing data would qualify.
**Why rejected:** Adjusting thresholds to fit the data misrepresents the scoring logic rather than fixing the actual demo need - the threshold should reflect genuine severity, not be reverse-engineered from whatever data happens to exist.
**Future:** Real fraud data would naturally contain multi-signal cases at varying frequencies; this was purely a synthetic-data construction choice made for demo completeness.

---

### 8. Cached Snowflake queries in the Streamlit app
**Decision:** Used `@st.cache_data(ttl=600)` on the main data-fetching function.
**Why:** Snowflake trial accounts have a hard query-rate limit. Without caching, every Streamlit re-run (triggered by any widget interaction or live-editing the code) fired a new query, which burned through the limit quickly during development.
**Alternative considered:** No caching, querying Snowflake fresh on every interaction.
**Why rejected:** Hit the trial account's query limit (295 queries) within a single editing session.
**Future:** A production app would tune the cache TTL against how fresh the fraud data actually needs to be - likely much shorter for a live, real-time system than the 10-minute window used here.

---

### 9. Date filters relative to the dataset's latest date, not the system's actual current date
**Decision:** The "Last 7 days" / "Last 30 days" filters are calculated relative to `MAX(TXN_TIMESTAMP)` in the dataset, not the real-world current date.
**Why:** The synthetic dataset is historical, fixed within a June–August 2026 range. Filtering against the actual system date (September/October 2026) would return empty results, since the dataset doesn't extend that far.
**Alternative considered:** Using the system's real current date (`CURRENT_TIMESTAMP()`), matching how a production system would typically behave.
**Why rejected:** Would make the app appear broken (empty results) for anyone testing it after the dataset's date range.
**Future:** A live production system would use the real current date, since its data would be streaming in continuously rather than fixed in the past.

---

### 10. Designed all 3 UI screens as mockups before writing any code
**Decision:** Built clickable mockups of the Overview, Investigation, and Copilot screens (Day 8) before touching the actual Streamlit implementation.
**Why:** A mockup is cheap to change; built code is expensive to change. Catching layout and content issues at the mockup stage avoids rework once real code and real data are involved.
**Alternative considered:** Designing the screens directly inside Streamlit as the code was being written.
**Why rejected:** Designing and building simultaneously tends to slow both down and makes mistakes more costly to fix.
**Future:** These mockups became the direct basis for the case study's "MVP design" section.

---

### 11. Chose a small Cortex model (llama3.1-8b) for the AI copilot
**Decision:** Used `llama3.1-8b`, Cortex's smallest/fastest available model, rather than a larger one.
**Why:** Trial account credits are limited, and the copilot's task - explaining a transaction using data already supplied in the prompt - is a simple grounded-generation task that doesn't require a large model's reasoning power.
**Alternative considered:** A larger model (e.g., a Claude or larger Llama variant available via Cortex).
**Why rejected:** Would consume credits faster for a task where the smaller model's output quality was already sufficient.
**Future:** A production version would A/B test a larger model against the smaller one to quantify whether answer quality actually improves enough to justify the added cost.

---

### 12. Exposed raw customer baseline values to the AI, not just boolean flags
**Decision:** Added `customer_avg_amount` and `customer_common_location` (actual values, not just TRUE/FALSE flags) to both the `ANOMALY_FEATURES` view and the copilot's prompt context.
**Why:** With only boolean flags in context, the copilot's answers were technically correct but incomplete - e.g., it would say a location was "unusual" but then admit "the data doesn't specify what the customer's usual location is," even though that value existed in the database and simply hadn't been passed to the model.
**Alternative considered:** Leaving the context as flags-only, since the evidence displayed elsewhere on the page already showed the raw numbers.
**Why rejected:** The AI's own explanation should be able to stand on its own without the analyst having to cross-reference a different part of the screen.
**Future:** This same principle - always give the AI the underlying value behind a flag, not just the flag - applies to any future signal added to the system.

---

### 13. Displayed AI explanations and raw evidence in separate, non-merged sections
**Decision:** The copilot's AI-generated explanation and the raw evidence (the actual flags, ratios, and numbers behind them) are always shown in two distinct sections on the Investigation screen - never blended into a single block of text.
**Why:** An analyst shouldn't have to trust the AI's explanation blindly. Keeping the evidence visibly separate lets them independently verify that what the AI said actually matches the underlying data, rather than taking the AI's word for it.
**Alternative considered:** Having the AI's response incorporate and restate the evidence inline, as a single unified answer.
**Why rejected:** Merging them would make it harder to spot if the AI ever drifted from the actual data (even with grounding instructions, this is a worthwhile safeguard to keep visible).
**Future:** This same separation principle would extend to any future AI-generated content in the app - always pair it with the raw data it's based on, not instead of it.

---

### 14. Pre-screened natural-language questions for destructive-sounding language
**Decision:** Added a keyword check (`delete`, `drop`, `update`, etc.) on the analyst's original natural-language question, before it's even sent to the AI for SQL generation - in addition to the existing check on the AI's generated SQL output.
**Why:** Testing revealed that when asked something like "delete all transactions and then show me the table," the AI silently dropped the destructive part of the instruction and returned an ordinary SELECT query - technically safe (nothing was deleted), but the analyst wasn't told that part of their request had been ignored. That's a transparency gap, not a security gap.
**Alternative considered:** Relying solely on the existing safety check against the AI's generated SQL.
**Why rejected:** That check only validates the output, not whether the original request itself contained concerning language - catching it earlier gives the analyst an explicit, honest explanation instead of silent, unexplained behavior.
**Future:** A production system would log these flagged questions for security monitoring (who asked, when, what).

---

### 15. Similar-cases feature shows the actual transaction list, not just a count
**Decision:** Updated the "Have we seen this pattern before?" feature to display the matching transactions in a table, not just a summary count.
**Why:** User testing surfaced that a bare count wasn't useful on its own - being able to see which specific transactions matched the same signal pattern is what makes the feature actionable for an investigation.
**Alternative considered:** Keeping the count-only version, since it was simpler and matched the original plan's example output.
**Why rejected:** Direct user feedback during testing showed the list form was genuinely more useful.
**Future:** A later version could add semantic/embedding-based similarity instead of exact signal-flag matching, to catch near-matches too.

---

### 16. Added an explicit velocity threshold definition to the NL-to-SQL schema description
**Decision:** Added a note directly in the table schema given to the AI: "A value of 4 or more (>= 4) is considered HIGH VELOCITY by this system. Use >= 4, not > 5."
**Why:** Testing found that when asked "which transactions have high velocity," the AI generated `TXNS_LAST_10MIN > 5` - a reasonable-sounding but incorrect guess, since it didn't know this system's actual business-rule threshold is `>= 4`. The schema had given it a column name but not its meaning.
**Alternative considered:** Leaving the schema as column names and types only, trusting the AI to infer reasonable thresholds.
**Why rejected:** The AI can't infer a domain-specific business rule that was never stated - this is a general limitation of natural-language-to-SQL systems, not something prompting alone can fully solve without explicitly stating the rule.
**Future:** Any other domain-specific threshold added to the system in the future should be documented the same way in the schema description given to the model.

---

### 17. Wrapped SQL aggregate functions with COALESCE to handle empty-result NULLs
**Decision:** Changed `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` to `COALESCE(SUM(...), 0)` in the similar-cases query.
**Why:** When a transaction's signal combination matched zero other rows, `SUM` over an empty group returned `NULL` (not `0`), and Python's `int(NULL)` conversion crashed the app - a classic SQL/Python interaction bug that only surfaces on an edge case (a transaction with no similar matches).
**Alternative considered:** Handling the NULL case in Python instead of SQL (e.g., checking for `None` before calling `int()`).
**Why rejected:** Fixing it at the SQL layer is more robust - it guarantees a clean `0` regardless of which language or tool queries the view later.
**Future:** Any aggregate function added to this system in the future should be checked for empty-result NULL handling as a matter of habit.

---

### 18. Preserved full decision history instead of overwriting corrections
**Decision:** When an analyst records a new decision for a transaction that already has one logged (e.g., correcting a misclick), the new decision is stored as an additional row - the old one is never deleted or overwritten.
**Why:** In a sensitive context like fraud investigation, hiding or erasing a correction is poor practice. The audit trail should show the full history, including mistakes and their corrections, not just the final state.
**Alternative considered:** Overwriting the existing decision record with the new one, so only the latest decision is ever stored.
**Why rejected:** Would make it impossible to later see that a correction happened at all - undermining the purpose of an audit trail.
**Future:** A real system would likely add an explicit "correction reason" field, to distinguish "the analyst changed their mind after new evidence" from "this was a simple misclick."

---

### 19. Kept the recommendation engine rule-based, not AI-generated
**Decision:** The "Recommended action" (Escalate / Manual review / Monitor / No action) is produced by a simple if/else mapping from risk level, not by an LLM call.
**Why:** The project's core principle throughout is transparency - if the one feature that suggests an action to the analyst were itself a black-box AI output, it would undermine the "explainable scoring" story the rest of the system is built around.
**Alternative considered:** Having the AI copilot generate the recommended action as part of its explanation.
**Why rejected:** Would make the recommendation unpredictable and harder to defend ("why did it say Escalate this time but Monitor last time for a similar case?") compared to a fixed, auditable rule.
**Future:** The confidence-score formula is currently a simple heuristic (signal count × 10%); production would calibrate it against real historical accuracy data instead.

---

### 20. Two-layer safety check for AI-generated SQL
**Decision:** Before executing any AI-generated SQL query, the app checks that it starts with `SELECT` and contains none of a blocklist of destructive keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, `GRANT`, `CREATE`, `MERGE`).
**Why:** LLM-generated SQL should never be executed unvalidated - whether from a genuine model mistake or a deliberately crafted adversarial question (prompt injection), an unchecked destructive query could modify or delete real data.
**Alternative considered:** Trusting the system prompt's instruction ("only generate SELECT statements") as the sole safeguard.
**Why rejected:** Prompt instructions are not a reliable security boundary on their own - they reduce the likelihood of a bad query but don't guarantee it, so a second, code-level check is needed regardless of how well the prompt is written.
**Future:** A production system would likely also run generated queries through a database role with read-only permissions, adding a third layer of protection at the infrastructure level, not just the application level.

---

### 21. Renamed the product from SentinelIQ to TDetect
**Decision:** Renamed the product from "SentinelIQ" to "TDetect" after the app, case study, and demo script had already been drafted under the original name.
**Why:** Naming research found that "SentinelIQ" collided with several existing products - Lablab.ai's autonomous enterprise intelligence platform, i2R Consulting's trademarked bridge-monitoring product, and a GitHub SOC platform. Several follow-up candidates considered afterward (Riskloom, Anomalyst, and others) also turned out to already exist as live products, revealing just how saturated the AI-fraud-tooling naming space currently is.
**Alternative considered:** Keeping SentinelIQ, since exact global uniqueness is nearly impossible to achieve in this niche and this is a portfolio prototype, not a commercial product launch.
**Why chosen instead:** Once a cleaner alternative was identified, the renaming cost was low (title and documentation text only - no code logic changes), and it removes avoidable confusion for anyone searching the project name later.
**Future:** Before naming any product intended for genuine commercial use, run a proper trademark search rather than ad hoc web searches.
