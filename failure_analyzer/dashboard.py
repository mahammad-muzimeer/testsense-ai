import re

import requests
import pandas as pd
import streamlit as st
from failure_classifier import analyze_failure

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TestSense AI",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 TestSense AI")
st.caption("Automated Test Failure Analysis Dashboard")

if st.button("🔄 Refresh Dashboard"):
    st.rerun()

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

run_id = analytics.get("run_id")

if run_id is not None:
    st.caption(f"Latest Test run ID: {run_id}")
else:
    st.warning("No tracked test run found.")

st.subheader("Test Run Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total tests", analytics.get("total", 0))
col2.metric("Passed", analytics.get("passed", 0))
col3.metric("Failed", analytics.get("failed", 0))
col4.metric("Expected Failures", analytics.get("expected_failures", 0))
col5.metric("Pass Rate", f'{analytics["pass_percentage"]}%')

st.divider()

# Failure category chart
st.subheader("Failure Category")

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
    st.info("No failure categories recorded yet.")

st.divider()

st.subheader("Historical Test Trends")

if history:
    history_df = pd.DataFrame(history)

    st.line_chart(
        history_df.set_index("run_id")[
            ["pass_percentage"]
        ]
    )

    st.line_chart(
        history_df.set_index("run_id")[
            ["passed", "failed", "expected_failures"]
        ]
    )
else:
    st.info("No historical test runs available yet.")

st.divider()

# Test results table
st.subheader("Recent Test Results")

# Always initialize the DataFrame, even when no results exist.
results_df = pd.DataFrame(results)

def format_duration(seconds):
    if seconds is None or pd.isna(seconds):
        return "N/A"

    seconds = float(seconds)

    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"

    return f"{seconds:.2f} s"

if results:
    results_df = pd.DataFrame(results)

    # Filter by test status
    statuses = ["All"] + sorted(
        results_df["status"].dropna().unique().tolist()
    )
    selected_status = st.selectbox("Filter by status", statuses, key="status_filter")

    filtered_df = results_df.copy()

    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

    # Filter by failure category, if available
    if "category" in filtered_df.columns:
        categories = ["All"] + sorted(
            filtered_df["category"].dropna().astype(str).unique().tolist()
        )
        selected_category = st.selectbox(
            "Filter by category",
            categories,
            key="category_filter",
        )

        if selected_category != "All":
            filtered_df = filtered_df[
                filtered_df["category"].astype(str) == selected_category
            ]

    # Create a display-only copy so the original data stays unchanged
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
    st.caption(f"Showing {len(filtered_df)} test result(s).")
else:
    st.info("No test results found in the database.")


# Export test results to CSV
st.subheader("Export Test Results")
if not results_df.empty:
    csv_data = results_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Test Results (CSV)",
        data=csv_data,
        file_name="testsense_test_results.csv",
        mime="text/csv",
    )
else:
    st.info("No test results available to export.")

st.divider()

# Test failure analysis
st.subheader("Failure Analysis")

if results:
    failed_results = [
        result for result in results
        if str(result.get("status", "")).strip().lower() in ("failed", "xfailed")
    ]

    if failed_results:
        selected_test = st.selectbox(
            "Select a failed test to investigate",
            failed_results,
            format_func=lambda test: test.get("test_name", "Unknown test"),
            key="failure_analysis_test",
        )

        analysis = analyze_failure(
            selected_test.get("error") or "",
            selected_test.get("traceback") or "",
        )

        # Summary cards
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Failure Category",
                analysis.get("category", "Unknown Failures"),
            )

        with col2:
            st.metric(
                "Analysis Confidence",
                analysis.get("confidence", "N/A"),
            )

        # Diagnosis
        st.markdown("### 🩺 Diagnosis")

        with st.container(border=True):
            st.markdown(f"**Likely cause**")
            st.write(
                analysis.get(
                    "likely_cause",
                    "No likely cause could be determined.",
                )
            )

            st.markdown("**Evidence**")
            st.code(
                str(analysis.get("evidence") or "No evidence available."),
                language=None,
            )

        # Recommended actions
        st.markdown("### 🛠️ Recommended troubleshooting")

        suggestions = analysis.get("suggestions", [])

        if suggestions:
            for index, suggestion in enumerate(suggestions, start=1):
                st.markdown(f"**{index}.** {suggestion}")
        else:
            st.info("No troubleshooting suggestion are available.")

        # Technical details
        with st.expander("🔎 View technical details", expanded=False):
            error_text = str(
                selected_test.get("error") or "No error message available."
            )
            traceback_text = str(
                selected_test.get("traceback") or "No traceback available."
            )
            # Remove ANSI terminal color/control sequences.
            ansi_pattern = re.compile(
                r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
            )

            error_text = ansi_pattern.sub("", error_text)
            traceback_text = ansi_pattern.sub("", traceback_text)

            st.markdown("**Error message**")
            st.code(error_text, language=None)

            st.markdown("**Traceback**")
            st.code(traceback_text, language="python")

    else:
        st.success("🎉 No failed tests in the latest run.")

else:
    st.info("No test results available for analysis.")

# Export failure analysis report
st.subheader("Export Failure Analysis Report")

if results:
    failed_results = [
        result for result in results
        if str(result.get("status", "")).strip().lower()
        in ("failed", "xfailed")
    ]

    if failed_results:
        report_rows = []

        for test in failed_results:
            analysis = analyze_failure(
                test.get("error") or "",
                test.get("traceback") or "",
            )

            report_rows.append({
                "Test Name": test.get("test_name", ""),
                "Status": test.get("status", ""),

                # use the actual failure analysis output
                "Failure Category": analysis.get(
                    "category",
                    test.get("category", "Unknown Failures"),
                ),
                "Confidence": analysis.get("confidence", "N/A"),
                "Evidence": analysis.get("evidence", ""),
                "Error Message": test.get("error") or "",
                "Likely Cause": analysis.get("likely_cause", ""),

                "Suggested Fixes": " | ".join(
                    str(item) for item in analysis.get("suggestions", [])
                ),
                "Traceback": test.get("traceback") or "",
                "Duration": test.get("duration", 0),
            })

        report_df = pd.DataFrame(report_rows)

        csv_report = report_df.to_csv(
            index=False,
        ).encode("utf-8")

        st.download_button(
            label="Download Failure Analysis Report (CSV)",
            data=csv_report,
            file_name="testsense_failure_report.csv",
            mime="text/csv",
            key="download_failure_analysis",
        )

        st.caption(
            f"Report includes {len(report_df)} failed or expected-failures test(s)."
        )
    else:
        st.info("No failure analysis records available to export.")
else:
    st.info("No test results available to export.")
