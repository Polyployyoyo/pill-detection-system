import streamlit as st

from components.layout import (
    render_header,
    render_divider,
    render_error,
    render_success,
)
from services.locker_api import get_lockers, add_quantity


def main() -> None:
    """Render the Inventory page for increasing drug quantities."""
    render_header(
        "Inventory Management - Add Stock",
        "Select a locker item and add pills to its quantity.",
    )

    render_divider()

    # Load all locker items
    try:
        inventories = get_lockers()
    except Exception as exc:
        render_error(f"Failed to load inventories: {exc}")
        return

    if not inventories:
        st.info("No locker records found.")
        return

    # Build dropdown options with a placeholder
    placeholder_label = "Please select a locker item"
    options = {
        f"Locker: {inv.get('locker_name')} - Slot: {inv.get('slot_code')} - "
        f"Drug: {inv.get('trade_name')} - Current quantity: {inv.get('quantity', 0)}": inv
        for inv in inventories
    }
    option_labels = [placeholder_label] + list(options.keys())

    # Keep selected option in session_state so we can reset after confirm
    if "locker_selected_label" not in st.session_state:
        st.session_state["locker_selected_label"] = placeholder_label

    selected_label = st.selectbox(
        "Select locker item to add stock",
        option_labels,
        index=(
            option_labels.index(st.session_state["locker_selected_label"])
            if st.session_state["locker_selected_label"] in option_labels
            else 0
        ),
    )
    st.session_state["locker_selected_label"] = selected_label

    if selected_label == placeholder_label:
        selected_locker = None
        selected_locker_id = None
        selected_drug_id = None
        current_quantity = 0
    else:
        selected_locker = options[selected_label]
        selected_locker_id = selected_locker.get("locker_id")
        selected_drug_id = selected_locker.get("drug_id")
        current_quantity = selected_locker.get("quantity", 0)

    render_divider()

    st.subheader("Add quantity")
    if selected_locker is None:
        st.info("Please select a locker item before adding quantity.")
    else:
        st.markdown(f"**Current quantity:** {current_quantity}")

    # Input for amount to add (positive integer)
    amount_str = st.text_input("Amount to add (must be a positive integer)", value="0")

    valid_amount = None
    if amount_str.strip():
        try:
            parsed = int(amount_str)
            if parsed > 0:
                valid_amount = parsed
            else:
                render_error("Amount must be a positive integer.")
        except ValueError:
            render_error("Amount must be a positive integer.")

    # Simple confirmation dialog using a checkbox + button pattern
    confirm = st.checkbox(
        "I confirm that I want to add this amount to the selected locker item."
    )

    if st.button("Confirm add quantity", type="primary"):
        if not confirm:
            render_error("Please tick the confirmation checkbox before proceeding.")
            return

        if selected_locker_id is None:
            render_error(
                "Selected item does not include locker_id from API. Please update server response to include locker_id."
            )
            return

        if selected_drug_id is None:
            render_error(
                "Selected item does not include drug_id from API. Please update server response to include drug_id."
            )
            return

        if valid_amount is None:
            render_error("Please provide a valid positive integer amount.")
            return

        try:
            updated = add_quantity(
                int(selected_locker_id),
                int(selected_drug_id),
                valid_amount,
            )
            new_quantity = updated.get("quantity", "unknown")
            render_success(
                f"Successfully added {valid_amount} pill(s). "
                f"New quantity: {new_quantity}."
            )

            # Reset dropdown back to placeholder after successful update
            st.session_state["locker_selected_label"] = placeholder_label
        except Exception as exc:
            render_error(f"Failed to update locker quantity: {exc}")


if __name__ == "__main__":
    main()
