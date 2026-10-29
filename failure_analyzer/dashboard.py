
import re

import pandas as pd
import requests
import streamlit as st
from failure_classifier import analyze_failure


API_URL = "http://127.0.0.1:8000"
FAILED_STATUSES = {"failed", "xfailed"}

st.set_page_config(
    page_title="TestSense AI",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 TestSense AI")
st.caption("Automated Test Failure Analysis Dashboard")

if st.button("🔄 Refresh Dashboard"):
    st.rerun()


# ---------------------------------------------------------
# Fetch data from the API
# ---------------------------------------------------------
try:
    analytics_response = requests.get(
        f"{API_URL}/analytics",
        timeout=10,
    )
    analytics_response.raise_for_status()
    analytics = analytics_response.json()

    history_response = requests.get(
        f"{API_URL}/analytics/history",
        timeout=10,
    )
    history_response.raise_for_status()
    history = history_response.json().get("history", [])

    results_response = requests.get(
        f"{API_URL}/results?limit=100",
        timeout=10,
    )
    results_response.raise_for_status()
    results = results_response.json().get("results", [])

except requests.RequestException as error:
    st.error(f"Could not connect to the API: {error}")
    st.info(
        "Start the FastAPI server in another terminal, "
        "then refresh this dashboard."
    )
    st.stop()


# ---------------------------------------------------------
# Prepare shared data
# ---------------------------------------------------------
results_df = pd.DataFrame(results)
history_df = pd.DataFrame(history)

failed_results = [
    result
    for result in results
    if str(result.get("status", "")).strip().lower()
    in FAILED_STATUSES
]

# Analyze failures once so the diagnosis and CSV report agree.
failure_records = []

for test in failed_results:
    analysis = analyze_failure(
        test.get("error") or "",
        test.get("traceback") or "",
    )

    failure_records.append({
        "test": test,
        "analysis": analysis,
    })


def format_duration(seconds):
    """Convert a duration in seconds into a readable value."""
    if seconds is None or pd.isna(seconds):
        return "N/A"

    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return "N/A"

    if seconds < 0:
        return "N/A"

    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"

    return f"{seconds:.2f} s"


def clean_terminal_text(value):
    """Remove ANSI terminal color/control sequences."""
    text = str(value or "")

    ansi_pattern = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    return ansi_pattern.sub("", text)


# ---------------------------------------------------------
# Header information
# ---------------------------------------------------------
run_id = analytics.get("run_id")

if run_id is not None:
    st.caption(f"Latest tracked test run: #{run_id}")
else:
    st.warning("No tracked test run found.")


# ---------------------------------------------------------
# Navigation
# ---------------------------------------------------------
overview_tab, results_tab, failure_tab, reports_tab = st.tabs([
    "📊 Overview",
    "🧪 Test Results",
    "🔍 Failure Analysis",
    "📥 Reports",
])


# =========================================================
# TAB 1: OVERVIEW
# =========================================================
with overview_tab:
    st.subheader("Test Run Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Tests", analytics.get("total", 0))
    col2.metric("Passed", analytics.get("passed", 0))
    col3.metric("Failed", analytics.get("failed", 0))
    col4.metric(
        "Expected Failures",
        analytics.get("expected_failures", 0),
    )
    col5.metric(
        "Pass Rate",
        f'{analytics.get("pass_percentage", 0)}%',
    )

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Failure Categories")

        categories = analytics.get("failure_categories", [])

        if categories:
            category_df = pd.DataFrame(
                categories,
                columns=["Category", "Occurrences"],
            )

            st.bar_chart(
                category_df.set_index("Category"),
                y="Occurrences",
            )
        else:
            st.success("No failure categories recorded.")

    with chart_col2:
        st.subheader("Pass Rate Trend")

        if not history_df.empty and {
            "run_id",
            "pass_percentage",
        }.issubset(history_df.columns):
            trend_df = history_df.sort_values("run_id")

            st.line_chart(
                trend_df.set_index("run_id")[["pass_percentage"]]
            )
        else:
            st.info("Historical pass-rate data is not available yet.")

    st.subheader("Test Execution Trend")

    trend_columns = [
        column
        for column in ["passed", "failed", "expected_failures"]
        if column in history_df.columns
    ]

    if not history_df.empty and "run_id" in history_df.columns and trend_columns:
        trend_df = history_df.sort_values("run_id")

        st.line_chart(
            trend_df.set_index("run_id")[trend_columns]
        )
    else:
        st.info("Historical execution data is not available yet.")

    if failed_results:
        st.warning(
            f"{len(failed_results)} failed or expected-failure "
            "test result(s) are available for investigation."
        )
    else:
        st.success("No failed or expected-failure results were returned.")


# =========================================================
# TAB 2: TEST RESULTS
# =========================================================
with results_tab:
    st.subheader("Recent Test Results")

    if not results_df.empty:
        filtered_df = results_df.copy()

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            statuses = ["All"]

            if "status" in results_df.columns:
                statuses += sorted(
                    results_df["status"].dropna().astype(str).unique().tolist()
                )

            selected_status = st.selectbox(
                "Filter by status",
                statuses,
                key="results_status_filter",
            )

        with filter_col2:
            categories = ["All"]

            if "category" in results_df.columns:
                categories += sorted(
                    results_df["category"].dropna().astype(str).unique().tolist()
                )

            selected_category = st.selectbox(
                "Filter by failure category",
                categories,
                key="results_category_filter",
            )

        if selected_status != "All" and "status" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["status"].astype(str) == selected_status
            ]

        if selected_category != "All" and "category" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["category"].astype(str) == selected_category
            ]

        display_df = filtered_df.copy()

        if "duration" in display_df.columns:
            display_df["duration"] = display_df["duration"].apply(
                format_duration
            )

        columns_to_show = [
            column
            for column in [
                "id",
                "test_name",
                "status",
                "category",
                "duration",
                "created_at",
            ]
            if column in display_df.columns
        ]

        st.dataframe(
            display_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
        )

        st.caption(f"Showing {len(filtered_df)} result(s).")
    else:
        st.info("No test results found in the database.")


# =========================================================
# TAB 3: FAILURE ANALYSIS
# =========================================================
with failure_tab:
    st.subheader("Failure Diagnosis")

    if failure_records:
        selected_index = st.selectbox(
            "Select a failed test to investigate",
            range(len(failure_records)),
            format_func=lambda index: (
                failure_records[index]["test"].get(
                    "test_name",
                    "Unknown test",
                )
            ),
            key="failure_analysis_test",
        )

        selected_record = failure_records[selected_index]
        selected_test = selected_record["test"]
        analysis = selected_record["analysis"]

        metric_col1, metric_col2 = st.columns(2)

        with metric_col1:
            st.metric(
                "Failure Category",
                analysis.get(
                    "category",
                    selected_test.get("category", "Unknown Failure"),
                ),
            )

        with metric_col2:
            st.metric(
                "Analysis Confidence",
                analysis.get("confidence", "N/A"),
            )

        st.markdown("### 🩺 Likely Cause")

        with st.container(border=True):
            st.write(
                analysis.get(
                    "likely_cause",
                    "No likely cause could be determined.",
                )
            )

            st.markdown("**Supporting evidence**")

            st.code(
                str(analysis.get("evidence") or "No evidence available."),
                language=None,
            )

        st.markdown("### 🛠️ Recommended Troubleshooting")

        suggestions = analysis.get("suggestions", [])

        if suggestions:
            for index, suggestion in enumerate(suggestions, start=1):
                st.markdown(f"**{index}.** {suggestion}")
        else:
            st.info("No troubleshooting suggestions are available.")

        with st.expander("🔎 View Technical Details", expanded=False):
            st.markdown("**Error message**")
            st.code(
                clean_terminal_text(selected_test.get("error")),
                language=None,
            )

            st.markdown("**Traceback**")
            st.code(
                clean_terminal_text(selected_test.get("traceback")),
                language="python",
            )

    else:
        st.success("🎉 No failed or expected-failure tests to investigate.")


# =========================================================
# TAB 4: REPORTS
# =========================================================
with reports_tab:
    st.subheader("Export Test Results")

    if not results_df.empty:
        results_csv = results_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Test Results (CSV)",
            data=results_csv,
            file_name="testsense_test_results.csv",
            mime="text/csv",
            key="download_test_results",
        )
    else:
        st.info("No test results are available to export.")

    st.divider()

    st.subheader("Export Failure Analysis Report")

    if failure_records:
        report_rows = []

        for record in failure_records:
            test = record["test"]
            analysis = record["analysis"]

            report_rows.append({
                "Test Name": test.get("test_name", ""),
                "Status": test.get("status", ""),
                "Failure Category": analysis.get(
                    "category",
                    test.get("category", "Unknown Failure"),
                ),
                "Confidence": analysis.get("confidence", "N/A"),
                "Evidence": analysis.get("evidence", ""),
                "Error Message": clean_terminal_text(test.get("error")),
                "Likely Cause": analysis.get("likely_cause", ""),
                "Suggested Fixes": " | ".join(
                    str(item)
                    for item in analysis.get("suggestions", [])
                ),
                "Traceback": clean_terminal_text(test.get("traceback")),
                "Duration": test.get("duration", 0),
            })

        report_df = pd.DataFrame(report_rows)

        report_csv = report_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Download Failure Analysis Report (CSV)",
            data=report_csv,
            file_name="testsense_failure_report.csv",
            mime="text/csv",
            key="download_failure_analysis",
        )

        st.caption(
            f"Report includes {len(report_df)} failed or expected-failure "
            "test result(s)."
        )
    else:
        st.info("No failure analysis records are available to export.")
