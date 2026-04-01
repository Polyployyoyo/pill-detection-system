from datetime import datetime

import requests
import streamlit as st

from components.layout import render_divider, render_error, render_header
from services.log_api import delete_log, get_logs


DELETE_BUTTON_STYLE = """
<style>
button[kind="secondary"] {
    border-color: #dc2626 !important;
    color: #dc2626 !important;
}
button[kind="secondary"]:hover {
    background-color: #fee2e2 !important;
    color: #b91c1c !important;
    border-color: #b91c1c !important;
}
</style>
"""


def load_logs() -> list[dict]:
    """Load detection logs from API."""
    try:
        return get_logs()
    except requests.RequestException as exc:
        render_error(f"Failed to load logs: {exc}")
        return []


def format_local_datetime(raw_value) -> str:
    """Convert an ISO datetime value into local machine datetime string."""
    if raw_value in (None, ""):
        return "-"

    try:
        parsed = datetime.fromisoformat(str(raw_value))
        return parsed.astimezone().strftime("%d %B %Y %H:%M:%S")
    except (TypeError, ValueError):
        return str(raw_value)


def normalize_log_rows(rows: list[dict]) -> list[dict]:
    """Normalize API log fields to table columns for display."""
    normalized_rows: list[dict] = []
    for row in rows:
        normalized_rows.append(
            {
                "Log ID": row.get("id", "-"),
                "Drug ID": row.get("drug_id", "-"),
                "Trade Name": row.get("trade_name", "-"),
                "Detected Quantity": row.get("detected_quantity", 0),
                "Confidence (%)": (
                    f"{float(row.get('confidence', 0.0)) * 100:.2f}"
                    if row.get("confidence") is not None
                    else "-"
                ),
                "Detected At": format_local_datetime(row.get("detected_at")),
            }
        )

    return normalized_rows


@st.dialog("Confirm Delete Log")
def confirm_delete_dialog(log_id: int) -> None:
    """Render a confirmation dialog before deleting a log."""
    st.write(f"Are you sure you want to delete log ID `{log_id}`?")
    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button("Yes, Delete", key=f"confirm_delete_{log_id}", type="primary"):
            try:
                delete_log(log_id)
                st.success(f"Deleted log ID {log_id} successfully.")
                st.rerun()
            except requests.RequestException as exc:
                render_error(f"Failed to delete log: {exc}")

    with cancel_col:
        if st.button("Cancel", key=f"cancel_delete_{log_id}"):
            st.rerun()


def render_logs_table_with_actions(display_rows: list[dict]) -> None:
    """Render logs as rows with a delete action on the right."""
    headers = [
        "Log ID",
        "Drug ID",
        "Drug Name",
        "Detected Quantity",
        "Confidence (%)",
        "Detected At",
        "Action",
    ]
    column_widths = [0.8, 0.8, 1.6, 1.4, 1.4, 2.2, 1]

    header_columns = st.columns(column_widths)
    for index, header in enumerate(headers):
        header_columns[index].markdown(f"**{header}**")

    for row in display_rows:
        row_columns = st.columns(column_widths)
        row_columns[0].write(row["Log ID"])
        row_columns[1].write(row["Drug ID"])
        row_columns[2].write(row["Trade Name"])
        row_columns[3].write(row["Detected Quantity"])
        row_columns[4].write(row["Confidence (%)"])
        row_columns[5].write(row["Detected At"])

        log_id = row["Log ID"]
        with row_columns[6]:
            if st.button("Delete", key=f"delete_row_{log_id}"):
                confirm_delete_dialog(int(log_id))


def main() -> None:
    """Render the detection history page."""
    st.markdown(DELETE_BUTTON_STYLE, unsafe_allow_html=True)

    render_header(
        "Detection History",
    )

    render_divider()

    logs = load_logs()

    st.subheader("Detection Logs")
    if not logs:
        st.info("No log records found.")
        return

    display_rows = normalize_log_rows(logs)
    render_logs_table_with_actions(display_rows)


if __name__ == "__main__":
    main()
