# TDetect - Test Cases (Day 25)

Run each of these in the live Streamlit app and record the actual result. Check ✅ if it matches expected, ❌ if not (and note what happened).

## Risk scoring

| # | Test | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| 1 | Critical, all 4 signals | Select TXN-83003 | Risk score 100, Critical | | |
| 2 | Critical, all 4 signals (2nd) | Select TXN-83011 | Risk score 85, Critical | | |
| 3 | High, 3 signals | Select TXN-82001 or TXN-82008 | Risk score 80, High | | |
| 4 | Normal transaction | Pick any transaction NOT in the flagged table | Risk score 0-30, Low (not shown in flagged table at all) | | |

## Copilot (single transaction)

| # | Test | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| 5 | Grounded explanation | Select TXN-83003, ask "Why was this transaction flagged?" | Answer names amount ratio, new device, location, velocity - all matching the displayed evidence | | |
| 6 | No invented info | Select a High (not Critical) transaction, ask "Why was this transaction flagged?" | Answer only mentions signals actually flagged for that transaction, not ones that aren't true | | |
| 7 | Out-of-scope question | Ask something unrelated, e.g. "What is the capital of France?" | Copilot should say the data doesn't answer this, not make something up | | |

## Natural-language queries

| # | Test | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| 8 | Basic filter | Ask "Show me all critical transactions from new devices" | Generated SQL filters RISK_LEVEL='Critical' AND FLAG_NEW_DEVICE=TRUE; returns TXN-83003, TXN-83011 | | |
| 9 | Different phrasing, same intent | Ask "Which transactions have high velocity?" | Generated SQL filters on TXNS_LAST_10MIN >= 4; returns matching rows | | |
| 10 | Safety check | Try to ask something that sounds destructive, e.g. "Delete all low risk transactions" | App should refuse to execute (blocked keyword), not actually delete anything | | |

## Similar cases & decisions

| # | Test | Steps | Expected | Actual | Pass? |
|---|---|---|---|---|---|
| 11 | Similar cases count | Select TXN-83003, check "Have we seen this pattern before?" | Shows a similar-case count with matching characteristics listed | | |
| 12 | Decision recorded + audit trail | Select any transaction, click "Escalate" | Success message shown; new row appears in Audit Trail table at the bottom with correct transaction ID, action, and timestamp | | |

---

