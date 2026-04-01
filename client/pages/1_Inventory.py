import requests
import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime

from services.locker_api import get_lockers
from components.layout import render_header, render_divider, render_error


def load_inventories(keyword: str | None = None):
    """
    Load inventories from the API, optionally filtered by keyword.

    Args:
        keyword: Optional search keyword to filter inventories.

    Returns:
        List of inventory dictionaries (may be empty).
    """
    try:
        return get_lockers(keyword=keyword)
    except requests.RequestException as exc:
        render_error(f"Failed to load inventories: {exc}")
        return []


def format_local_datetime(raw_value: str | None) -> str:
    """Convert an ISO datetime string to local machine time and display format."""
    if not raw_value:
        return "-"

    try:
        parsed = datetime.fromisoformat(str(raw_value))
        return parsed.astimezone().strftime("%d %B %Y %H:%M:%S")
    except (ValueError, TypeError):
        return str(raw_value)


def normalize_inventory_rows(rows: list[dict]) -> list[dict]:
    """Rename columns and format datetime for table display."""
    normalized_rows: list[dict] = []
    for row in rows:
        normalized_rows.append(
            {
                "Locker Name": row.get("locker_name", "-"),
                "Slot Code": row.get("slot_code", "-"),
                "Drug Name": row.get("trade_name", "-"),
                "Quantity": row.get("quantity", 0),
                "Last Updated": format_local_datetime(row.get("last_updated")),
            }
        )
    return normalized_rows


def build_inventory_chart_rows(rows: list[dict]) -> list[dict]:
    """Transform inventory rows into chart-ready records."""
    chart_rows: list[dict] = []
    for row in rows:
        chart_rows.append(
            {
                "Inventory Item": (
                    f"{row.get('Locker Name', '-')}"
                    f" | {row.get('Slot Code', '-')}"
                    f" | {row.get('Drug Name', '-')}"
                ),
                "Quantity": row.get("Quantity", 0),
            }
        )
    return chart_rows


def render_inventory_quantity_chart(chart_rows: list[dict]) -> None:
    """Render a slimmer bar chart for inventory quantity."""
    chart_df = pd.DataFrame(chart_rows)
    bars = (
        alt.Chart(chart_df)
        .mark_bar(size=24)
        .encode(
            x=alt.X(
                "Inventory Item:N",
                sort="-y",
                axis=alt.Axis(labelAngle=-45, labelLimit=1000),
            ),
            y=alt.Y("Quantity:Q"),
            tooltip=["Inventory Item", "Quantity"],
        )
    )
    labels = bars.mark_text(
        align="center",
        baseline="bottom",
        dy=-4,
        fontSize=12,
    ).encode(text=alt.Text("Quantity:Q", format=","))

    st.altair_chart((bars + labels), use_container_width=True)


def main():
    """Render the Home page."""
    render_header(
        "Inventory",
        "View and filter drug inventories.",
    )

    with st.form("inventory_filter_form"):
        st.subheader("Filter Inventories")
        keyword_input = st.text_input(
            "Keyword",
            value="",
            help="Search by locker name, drug name, or slot code. Leave empty to show all.",
        )
        submitted = st.form_submit_button("Apply Filter")

    selected_keyword = None
    if submitted and keyword_input.strip():
        selected_keyword = keyword_input.strip()

    render_divider()

    inventories = load_inventories(selected_keyword)


    if not inventories:
        st.info("No inventories found for the given filter.")
        return

    display_rows = normalize_inventory_rows(inventories)
    st.subheader("Inventory Quantity Chart")
    chart_rows = build_inventory_chart_rows(display_rows)
    render_inventory_quantity_chart(chart_rows)

    st.subheader("Inventory Table")
    st.dataframe(display_rows, use_container_width=True)


if __name__ == "__main__":
    main()
