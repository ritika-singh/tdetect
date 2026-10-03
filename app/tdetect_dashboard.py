import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(layout="wide")
session = get_active_session()

st.title("TDetect")
st.caption("Fraud and anomaly investigation copilot")

RISK_BADGE = {"Critical": "🔴 Critical", "High": "🟠 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}
ACTION_BADGE = {
    "Escalate immediately": "🔴 Escalate immediately",
    "Manual review": "🟠 Manual review",
    "Monitor": "🟡 Monitor",
    "No action needed": "🟢 No action needed",
}

AMOUNT_COL_CONFIG = st.column_config.NumberColumn("Amount", format="₹%.2f")

tab1, tab2 = st.tabs(["Analyst View", "Manager View"])

with tab1:
    date_option = st.selectbox("Date range", ["All time", "Last 7 days", "Last 30 days", "Specific date"])

    selected_date = None
    if date_option == "Specific date":
        selected_date = st.date_input(
            "Pick a date",
            value=pd.Timestamp("2026-08-28"),
            min_value=pd.Timestamp("2026-06-01"),
            max_value=pd.Timestamp("2026-08-29")
        )

    @st.cache_data(ttl=600)
    def load_data(date_option, selected_date=None):
        query = "SELECT * FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES"
        if date_option == "Last 7 days":
            query += " WHERE TXN_TIMESTAMP >= DATEADD(day, -7, (SELECT MAX(TXN_TIMESTAMP) FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES))"
        elif date_option == "Last 30 days":
            query += " WHERE TXN_TIMESTAMP >= DATEADD(day, -30, (SELECT MAX(TXN_TIMESTAMP) FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES))"
        elif date_option == "Specific date" and selected_date:
            query += f" WHERE DATE(TXN_TIMESTAMP) = '{selected_date}'"
        return session.sql(query).to_pandas()

    with st.spinner("Loading transactions..."):
        df = load_data(date_option, selected_date)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total transactions", len(df))
    col2.metric("Anomalies flagged", int((df["RISK_SCORE"] > 0).sum()))
    col3.metric("High risk", int((df["RISK_LEVEL"] == "High").sum()))
    col4.metric("Critical", int((df["RISK_LEVEL"] == "Critical").sum()))

    st.subheader("Flagged transactions")
    flagged = df[df["RISK_LEVEL"].isin(["High", "Critical"])].sort_values("RISK_SCORE", ascending=False).copy()

    if len(flagged) == 0:
        st.info("No flagged transactions in this date range.")
    else:
        flagged_display = flagged.copy()
        flagged_display["RISK_LEVEL"] = flagged_display["RISK_LEVEL"].map(RISK_BADGE)
        display_cols = ["TRANSACTION_ID", "TXN_TIMESTAMP", "CUSTOMER_ID", "AMOUNT", "RISK_SCORE", "RISK_LEVEL"]
        st.dataframe(
            flagged_display[display_cols],
            width='stretch',
            hide_index=True,
            column_config={"AMOUNT": AMOUNT_COL_CONFIG}
        )

    st.subheader("Investigate a transaction")

    if len(flagged) == 0:
        st.info("No flagged transactions to investigate in this date range.")
    else:
        selected_txn = st.selectbox("Select a transaction", flagged["TRANSACTION_ID"].tolist())

        if selected_txn:
            detail_query = f"""
                SELECT * FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES
                WHERE TRANSACTION_ID = '{selected_txn}'
            """
            detail = session.sql(detail_query).to_pandas().iloc[0]

            st.markdown(f"### Risk score: {int(detail['RISK_SCORE'])} — {RISK_BADGE.get(detail['RISK_LEVEL'], detail['RISK_LEVEL'])}")

            c1, c2 = st.columns(2)
            with c1:
                st.write("**Customer:**", detail["CUSTOMER_ID"])
                st.write("**Amount:**", f"₹{detail['AMOUNT']:,.2f}")
                st.write("**Location:**", detail["LOCATION"])
            with c2:
                st.write("**Device:**", detail["DEVICE_ID"])
                st.write("**Time:**", detail["TXN_TIMESTAMP"])
                st.write("**Merchant:**", detail["MERCHANT_CATEGORY"])

            st.markdown("**Why was this flagged?**")
            evidence_lines = []
            if detail["FLAG_AMOUNT_ANOMALY"]:
                evidence_lines.append(f"- Amount anomaly: {detail['AMOUNT_RATIO']}x customer average")
            if detail["FLAG_NEW_DEVICE"]:
                evidence_lines.append("- New device not seen on this account before")
            if detail["FLAG_UNUSUAL_LOCATION"]:
                evidence_lines.append("- Unusual location for this customer")
            if detail["TXNS_LAST_10MIN"] >= 4:
                evidence_lines.append(f"- High velocity: {int(detail['TXNS_LAST_10MIN'])} transactions within 10 minutes")
            if detail["FLAG_UNUSUAL_MERCHANT"]:
                evidence_lines.append("- Unusual merchant category for this customer")

            if evidence_lines:
                for line in evidence_lines:
                    st.write(line)
            else:
                st.write("No individual signals met the threshold, but the combined score still triggered a flag.")

            st.divider()
            st.subheader("Ask the copilot about this transaction")

            user_question = st.text_input(
                "Ask about this transaction",
                placeholder="Why was this transaction flagged?"
            )

            if user_question:
                context = f"""
Transaction ID: {detail['TRANSACTION_ID']}
Customer: {detail['CUSTOMER_ID']}
Amount: {detail['AMOUNT']} (customer's average: {detail['CUSTOMER_AVG_AMOUNT']}, ratio: {detail['AMOUNT_RATIO']}x)
Location: {detail['LOCATION']} (customer's usual location: {detail['CUSTOMER_COMMON_LOCATION']})
Device: {detail['DEVICE_ID']}
Merchant category: {detail['MERCHANT_CATEGORY']}
Risk score: {detail['RISK_SCORE']} ({detail['RISK_LEVEL']})
Flags triggered:
- Amount anomaly: {bool(detail['FLAG_AMOUNT_ANOMALY'])}
- New device: {bool(detail['FLAG_NEW_DEVICE'])}
- Unusual location: {bool(detail['FLAG_UNUSUAL_LOCATION'])}
- High velocity ({int(detail['TXNS_LAST_10MIN'])} transactions in 10 min): {detail['TXNS_LAST_10MIN'] >= 4}
- Unusual merchant: {bool(detail['FLAG_UNUSUAL_MERCHANT'])}
"""
                system_instruction = (
                    "You are a fraud investigation assistant. Use ONLY the transaction data provided "
                    "below to answer the analyst's question. Do not invent any evidence or information "
                    "not explicitly present in the data. If the data is insufficient to answer, say so."
                )

                full_prompt = f"{system_instruction}\n\nTransaction data:\n{context}\n\nAnalyst question: {user_question}\n\nAnswer:"
                escaped_prompt = full_prompt.replace("'", "''")

                with st.spinner("Thinking..."):
                    cortex_query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', '{escaped_prompt}') AS response"
                    answer = session.sql(cortex_query).to_pandas().iloc[0]["RESPONSE"]

                st.markdown("**Copilot:**")
                st.write(answer)

            st.divider()
            st.subheader("Have we seen this pattern before?")

            similar_query = f"""
                SELECT TRANSACTION_ID, CUSTOMER_ID, TXN_TIMESTAMP, RISK_SCORE, RISK_LEVEL, IS_SYNTHETIC_ANOMALY
                FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES
                WHERE TRANSACTION_ID != '{selected_txn}'
                  AND FLAG_AMOUNT_ANOMALY = {bool(detail['FLAG_AMOUNT_ANOMALY'])}
                  AND FLAG_NEW_DEVICE = {bool(detail['FLAG_NEW_DEVICE'])}
                  AND FLAG_UNUSUAL_LOCATION = {bool(detail['FLAG_UNUSUAL_LOCATION'])}
                  AND FLAG_UNUSUAL_MERCHANT = {bool(detail['FLAG_UNUSUAL_MERCHANT'])}
                ORDER BY RISK_SCORE DESC
            """
            similar_df = session.sql(similar_query).to_pandas()
            similar_count = len(similar_df)

            if similar_count == 0:
                st.write("No similar cases found with this exact combination of signals.")
            else:
                st.write(f"**{similar_count} similar case(s)** found with this same combination of risk signals:")
                characteristics = []
                if detail["FLAG_AMOUNT_ANOMALY"]:
                    characteristics.append("Amount anomaly")
                if detail["FLAG_NEW_DEVICE"]:
                    characteristics.append("New device")
                if detail["FLAG_UNUSUAL_LOCATION"]:
                    characteristics.append("Unusual location")
                if detail["FLAG_UNUSUAL_MERCHANT"]:
                    characteristics.append("Unusual merchant")
                st.write("Common characteristics: " + ", ".join(characteristics))
                similar_display = similar_df.copy()
                similar_display["RISK_LEVEL"] = similar_display["RISK_LEVEL"].map(RISK_BADGE)
                st.dataframe(similar_display, width='stretch', hide_index=True)
                st.caption(
                    "IS_SYNTHETIC_ANOMALY here reflects this dataset's labeled anomaly set, used for "
                    "demo evaluation only — not real fraud-confirmation data."
                )

            st.divider()
            st.subheader("Recommended action")

            risk_level = detail["RISK_LEVEL"]
            risk_score = int(detail["RISK_SCORE"])

            signal_count = sum([
                bool(detail["FLAG_AMOUNT_ANOMALY"]),
                bool(detail["FLAG_NEW_DEVICE"]),
                bool(detail["FLAG_UNUSUAL_LOCATION"]),
                bool(detail["TXNS_LAST_10MIN"] >= 4),
                bool(detail["FLAG_UNUSUAL_MERCHANT"]),
            ])

            if risk_level == "Critical":
                action = "Escalate immediately"
            elif risk_level == "High":
                action = "Manual review"
            elif risk_level == "Medium":
                action = "Monitor"
            else:
                action = "No action needed"

            confidence = min(95, 50 + (signal_count * 10))

            st.markdown(f"**{ACTION_BADGE.get(action, action)}**")
            st.write(f"Confidence: {confidence}%")
            st.write(f"Reason: {signal_count} independent risk signal(s) detected.")
            st.caption("This is a recommendation only — the final decision stays with the analyst.")

            st.divider()
            st.subheader("Analyst decision")

            existing_query = f"""
                SELECT ANALYST_DECISION, DECISION_TIMESTAMP
                FROM SENTINELIQ_DB.CASES.FRAUD_CASES
                WHERE TRANSACTION_ID = '{selected_txn}'
                ORDER BY DECISION_TIMESTAMP DESC
            """
            existing = session.sql(existing_query).to_pandas()

            if len(existing) > 0:
                st.info(f"Already recorded as **{existing.iloc[0]['ANALYST_DECISION']}** on {existing.iloc[0]['DECISION_TIMESTAMP']}")

            b1, b2, b3 = st.columns(3)

            def record_decision(decision_value):
                insert_query = f"""
                    INSERT INTO SENTINELIQ_DB.CASES.FRAUD_CASES
                        (transaction_id, customer_id, risk_score, risk_level, recommended_action, analyst_decision)
                    VALUES
                        ('{selected_txn}', '{detail['CUSTOMER_ID']}', {risk_score}, '{risk_level}', '{action}', '{decision_value}')
                """
                session.sql(insert_query).collect()
                st.success(f"Recorded: {decision_value}")

            with b1:
                if st.button("Confirm Fraud", width='stretch'):
                    record_decision("Confirmed Fraud")
            with b2:
                if st.button("Mark Legitimate", width='stretch'):
                    record_decision("Marked Legitimate")
            with b3:
                if st.button("Escalate", width='stretch'):
                    record_decision("Escalated")

    st.divider()
    st.subheader("Ask across all transactions")

    nl_question = st.text_input(
        "Ask a question about your transactions",
        placeholder="Show me all critical transactions from new devices"
    )

    if nl_question:
        destructive_words = ["delete", "remove", "drop", "update", "insert", "truncate", "alter", "modify"]
        if any(word in nl_question.lower() for word in destructive_words):
            st.warning(
                "Your question contains language that sounds like it's asking to modify or delete data. "
                "This app only supports read (SELECT) queries — no data will be changed. "
                "Rephrase your question as something you'd like to view instead."
            )
        else:
            schema_description = """
Table: SENTINELIQ_DB.ANALYTICS.RISK_SCORES
Columns:
- TRANSACTION_ID (string)
- CUSTOMER_ID (string)
- TXN_TIMESTAMP (timestamp)
- AMOUNT (number)
- MERCHANT_CATEGORY (string)
- LOCATION (string)
- DEVICE_ID (string)
- CUSTOMER_AVG_AMOUNT (number)
- CUSTOMER_COMMON_LOCATION (string)
- AMOUNT_RATIO (number)
- FLAG_AMOUNT_ANOMALY (boolean)
- FLAG_NEW_DEVICE (boolean)
- FLAG_UNUSUAL_LOCATION (boolean)
- TXNS_LAST_10MIN (number): count of this customer's transactions in the preceding 10 minutes.
  A value of 4 or more (>= 4) is considered HIGH VELOCITY by this system. Use >= 4, not > 5.
- FLAG_UNUSUAL_MERCHANT (boolean)
- RISK_SCORE (number, 0-100)
- RISK_LEVEL (string: Low, Medium, High, Critical)
"""
            sql_system_instruction = f"""
You are a SQL generator. Convert the analyst's question into a single Snowflake SQL SELECT query
against this table only:

{schema_description}

Rules:
- Output ONLY the SQL query, nothing else. No explanation, no markdown formatting, no backticks.
- Only generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, or CREATE.
- Always include ORDER BY RISK_SCORE DESC unless the question asks for a different order.
- Always include LIMIT 50 unless the question specifies a different limit.
"""
            full_sql_prompt = f"{sql_system_instruction}\n\nQuestion: {nl_question}\n\nSQL:"
            escaped_sql_prompt = full_sql_prompt.replace("'", "''")

            with st.spinner("Generating query..."):
                sql_gen_query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', '{escaped_sql_prompt}') AS response"
                generated_sql = session.sql(sql_gen_query).to_pandas().iloc[0]["RESPONSE"].strip()

            generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
            st.code(generated_sql, language="sql")

            lowered = generated_sql.lower()
            forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "grant", "create", "merge"]
            is_safe = lowered.startswith("select") and not any(word in lowered for word in forbidden)

            if not is_safe:
                st.error("This query couldn't be safely executed. Try rephrasing your question.")
            else:
                try:
                    result_df = session.sql(generated_sql).to_pandas()
                    if len(result_df) == 0:
                        st.info("No transactions matched this question.")
                    else:
                        st.dataframe(result_df, width='stretch', hide_index=True)
                except Exception as e:
                    st.error(f"Query failed: {e}")

    st.divider()
    st.subheader("Audit trail")

    audit_query = """
        SELECT TRANSACTION_ID, CUSTOMER_ID, RISK_LEVEL, RECOMMENDED_ACTION, ANALYST_DECISION, DECISION_TIMESTAMP
        FROM SENTINELIQ_DB.CASES.FRAUD_CASES
        ORDER BY DECISION_TIMESTAMP DESC
        LIMIT 20
    """
    audit_df = session.sql(audit_query).to_pandas()
    if len(audit_df) == 0:
        st.info("No decisions recorded yet. Investigate a transaction above and record a decision to see it here.")
    else:
        audit_display = audit_df.copy()
        audit_display["RISK_LEVEL"] = audit_display["RISK_LEVEL"].map(RISK_BADGE)
        st.dataframe(audit_display, width='stretch', hide_index=True)

with tab2:
    st.header("Fraud Risk Overview")
    st.caption("Rolled-up view for risk managers")

    mgr_df = session.sql("SELECT * FROM SENTINELIQ_DB.ANALYTICS.RISK_SCORES").to_pandas()
    mgr_flagged = mgr_df[mgr_df["RISK_LEVEL"].isin(["High", "Critical"])]

    latest_decisions_query = """
        WITH latest AS (
            SELECT transaction_id, analyst_decision,
                   ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY decision_timestamp DESC) AS rn
            FROM SENTINELIQ_DB.CASES.FRAUD_CASES
        )
        SELECT analyst_decision, COUNT(*) AS cnt
        FROM latest
        WHERE rn = 1
        GROUP BY analyst_decision
    """
    decisions_df = session.sql(latest_decisions_query).to_pandas()

    confirmed_fraud_count = 0
    if len(decisions_df) > 0:
        match = decisions_df[decisions_df["ANALYST_DECISION"] == "Confirmed Fraud"]
        if len(match) > 0:
            confirmed_fraud_count = int(match.iloc[0]["CNT"])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total transactions", len(mgr_df))
    m2.metric("Anomalies", int((mgr_df["RISK_SCORE"] > 0).sum()))
    m3.metric("High risk", int((mgr_df["RISK_LEVEL"] == "High").sum()))
    m4.metric("Critical", int((mgr_df["RISK_LEVEL"] == "Critical").sum()))
    m5.metric("Confirmed fraud", confirmed_fraud_count)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Top anomaly signal")
        if len(mgr_flagged) > 0:
            signal_counts = {
                "Amount anomaly": int(mgr_flagged["FLAG_AMOUNT_ANOMALY"].sum()),
                "New device": int(mgr_flagged["FLAG_NEW_DEVICE"].sum()),
                "Unusual location": int(mgr_flagged["FLAG_UNUSUAL_LOCATION"].sum()),
                "High velocity": int((mgr_flagged["TXNS_LAST_10MIN"] >= 4).sum()),
                "Unusual merchant": int(mgr_flagged["FLAG_UNUSUAL_MERCHANT"].sum()),
            }
            top_signal = max(signal_counts, key=signal_counts.get)
            st.write(f"**{top_signal}** ({signal_counts[top_signal]} flagged transactions)")
        else:
            st.write("No flagged transactions yet.")

    with col_b:
        st.subheader("Most affected location")
        if len(mgr_flagged) > 0:
            top_location = mgr_flagged["LOCATION"].mode().iloc[0]
            location_count = int((mgr_flagged["LOCATION"] == top_location).sum())
            st.write(f"**{top_location}** ({location_count} flagged transactions)")
        else:
            st.write("No flagged transactions yet.")

    st.divider()
    st.subheader("Analyst decisions breakdown")
    if len(decisions_df) == 0:
        st.info("No decisions recorded yet.")
    else:
        st.dataframe(decisions_df, width='stretch', hide_index=True)
