import requests
import streamlit as st

from components.layout import render_divider, render_error, render_header, render_success
from services.locker_api import get_lockers, transfer_quantity


def load_inventories() -> list[dict]:
    """Load all locker inventory records."""
    try:
        return get_lockers()
    except requests.RequestException as exc:
        render_error(f"Failed to load inventories: {exc}")
        return []


def build_drug_choices(inventories: list[dict]) -> list[tuple[str, int]]:
    """Build unique drug choices as (label, drug_id)."""
    drug_map: dict[int, str] = {}
    for item in inventories:
        drug_id = item.get("drug_id")
        trade_name = item.get("trade_name")
        if drug_id is not None and trade_name:
            drug_map[int(drug_id)] = str(trade_name)

    return [
        (f"{trade_name} (Drug ID: {drug_id})", drug_id)
        for drug_id, trade_name in sorted(drug_map.items(), key=lambda x: x[1])
    ]


def build_locker_choices(items: list[dict]) -> list[tuple[str, int]]:
    """Build locker choices for a selected drug."""
    choices: list[tuple[str, int]] = []
    for item in items:
        locker_id = item.get("locker_id")
        if locker_id is None:
            continue
        label = (
            f"Locker {item.get('locker_name', '-')} | "
            f"Slot {item.get('slot_code', '-')} | "
            f"Available {item.get('quantity', 0)}"
        )
        choices.append((label, int(locker_id)))
    return choices


def get_item_by_locker_id(items: list[dict], locker_id: int) -> dict | None:
    """Find inventory item by locker ID."""
    for item in items:
        if int(item.get("locker_id", -1)) == locker_id:
            return item
    return None


def main() -> None:
    """Render the move inventory page."""
    render_header(
        "Inventory Management - Move Stock",
        "Move stock between lockers for the same drug.",
    )
    render_divider()

    inventories = load_inventories()
    if not inventories:
        st.info("No inventory records found.")
        return

    drug_choices = build_drug_choices(inventories)
    if not drug_choices:
        st.info("No valid drug records found for moving stock.")
        return

    selected_drug_label = st.selectbox(
        "Select drug to move",
        options=[label for label, _ in drug_choices],
    )
    selected_drug_id = next(
        drug_id for label, drug_id in drug_choices if label == selected_drug_label
    )

    same_drug_items = [
        item for item in inventories if int(item.get("drug_id", -1)) == selected_drug_id
    ]
    locker_choices = build_locker_choices(same_drug_items)
    if len(locker_choices) < 2:
        st.info("Need at least two lockers for this drug to perform a transfer.")
        return

    source_label = st.selectbox(
        "Source locker",
        options=[label for label, _ in locker_choices],
        key="source_locker",
    )
    source_locker_id = next(
        locker_id for label, locker_id in locker_choices if label == source_label
    )

    destination_options = [
        (label, locker_id)
        for label, locker_id in locker_choices
        if locker_id != source_locker_id
    ]
    destination_label = st.selectbox(
        "Destination locker",
        options=[label for label, _ in destination_options],
        key="destination_locker",
    )
    destination_locker_id = next(
        locker_id
        for label, locker_id in destination_options
        if label == destination_label
    )

    source_item = get_item_by_locker_id(same_drug_items, source_locker_id)
    destination_item = get_item_by_locker_id(same_drug_items, destination_locker_id)
    source_quantity = int(source_item.get("quantity", 0)) if source_item else 0
    destination_quantity = int(destination_item.get("quantity", 0)) if destination_item else 0

    st.caption(
        f"Source available: {source_quantity} pill(s) | "
        f"Destination current: {destination_quantity} pill(s)"
    )

    quantity_str = st.text_input(
        "Quantity to move (positive integer)",
        value="1",
    )

    confirm = st.checkbox("I confirm this stock transfer.")
    if st.button("Confirm move stock", type="primary"):
        if not confirm:
            render_error("Please tick the confirmation checkbox before proceeding.")
            return

        try:
            quantity = int(quantity_str.strip())
            if quantity <= 0:
                raise ValueError()
        except ValueError:
            render_error("Quantity to move must be a positive integer.")
            return

        if quantity > source_quantity:
            render_error("Transfer quantity exceeds available stock in source locker.")
            return

        try:
            result = transfer_quantity(
                source_locker_id=source_locker_id,
                destination_locker_id=destination_locker_id,
                drug_id=selected_drug_id,
                quantity=quantity,
            )
            source_after = result.get("source", {}).get("quantity", "unknown")
            destination_after = result.get("destination", {}).get("quantity", "unknown")
            render_success(
                f"Moved {quantity} pill(s) successfully. "
                f"Source now: {source_after}, destination now: {destination_after}."
            )
            st.rerun()
        except requests.RequestException as exc:
            render_error(f"Failed to move stock: {exc}")


if __name__ == "__main__":
    main()
