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

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Recorded results", analytics["total"])
col2.metric("Passed", analytics["passed"])
col3.metric("Failed", analytics["failed"])
col4.metric("Pass Rate", f'{analytics["pass_percentage"]}%')

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

# Test results table
st.subheader("Recent Test Results")

if results:
    df = pd.DataFrame(results)

    # Optional filters
    statuses = ["All"] + sorted(
        df["status"].dropna().unique().tolist()
    )
    selected_status = st.selectbox("Filter by status", statuses)

    if selected_status != "All":
        df = df[df["status"] == selected_status]

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
        if column in df.columns
    ]

    st.dataframe(
        df[columns_to_show],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No test results found in the database.")


# Test failure analysis
st.divider()
st.subheader("Failure Analysis")

if results:
    failed_results = [
        result for result in results
        if str(result.get("status", "")).strip().lower() in ("failed", "xfailed")
    ]

    if failed_results:
        selected_test = st.selectbox(
            "Select a failed test",
            failed_results,
            format_func=lambda test: test["test_name"]
        )

        analysis = analyze_failure(
            selected_test.get("error", ""),
            selected_test.get("traceback", "")
        )

        st.markdown(f"**Category**: {analysis['category']}")
        st.markdown(f"**Likely cause**")
        st.write(analysis["likely_cause"])

        st.markdown("**Suggested troubleshooting steps**")
        for suggestion in analysis["suggestions"]:
            st.markdown(f"- {suggestion}")

        with st.expander("View original error"):
            st.code(selected_test.get("error", "No error message"))
            st.code(selected_test.get("traceback", "No traceback"))

    else:
        st.info("No failed tests in the latest run.")

else:
    st.info("No test results available for analysis.")
