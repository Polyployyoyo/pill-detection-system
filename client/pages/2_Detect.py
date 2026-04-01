import io
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from services.drug_api import get_drugs, get_drug_by_id
from services.detect_api import DetectAPI
from services.locker_api import (
    subtract_quantity,
)
from services.log_api import create_log as create_detection_log
from utils.base64_to_image import base64_to_image
from components.layout import (
    render_header,
    render_divider,
    render_error,
    render_success,
)


load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def load_drugs():
    """
    Load all drugs for use in dropdowns.

    Returns:
        List of drug dictionaries (may be empty).
    """
    try:
        return get_drugs()
    except requests.RequestException as exc:
        render_error(f"Failed to load drugs: {exc}")
        return []


def detect_uploaded_image(uploaded_file) -> dict | None:
    """
    Send the uploaded image to the detect API.

    Args:
        uploaded_file: UploadedFile object from Streamlit.

    Returns:
        Detection result dictionary or None on failure.
    """
    if uploaded_file is None:
        return None

    try:
        api = DetectAPI()
        # Save to in-memory buffer so we do not need a temp file on disk
        image_bytes = uploaded_file.read()
        with io.BytesIO(image_bytes) as tmp_buffer:
            tmp_buffer.name = uploaded_file.name
            files = {"file": tmp_buffer}
            response = requests.post(api.detect_endpoint, files=files)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as exc:
        render_error(f"Detection failed: {exc}")
        return None


@st.dialog("Confirm pill counting and inventory update")
def confirm_pill_dialog(
    selected_drug: dict,
    selected_drug_id: int,
    matched_total: int,
    matched_confidence_value: float | None,
) -> None:
    """Dialog to confirm pill counting and update logs & inventory."""
    st.markdown(f"**Drug:** {selected_drug.get('trade_name', '-')}")
    st.markdown(f"**Drug ID:** {selected_drug_id}")
    st.markdown(f"**Detected quantity:** {matched_total} pill(s)")

    if matched_confidence_value is not None:
        st.markdown(f"**Average confidence:** {matched_confidence_value * 100:.2f}%")
    else:
        st.markdown("**Average confidence:** N/A")

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Confirm", key="confirm_detect_log"):
            try:
                # 1) Create detection log
                create_detection_log(
                    drug_id=int(selected_drug_id),
                    detected_quantity=int(matched_total),
                    confidence=float(
                        matched_confidence_value
                        if matched_confidence_value is not None
                        else 0.0
                    ),
                )

                # 2) Subtract quantity by drug ID (no inventory selection needed)
                subtract_quantity(1, int(selected_drug_id), int(matched_total))

                render_success(
                    "Detection log created and inventory updated successfully."
                )
            except requests.RequestException as exc:
                render_error(
                    f"Failed to create detection log or update inventory: {exc}"
                )

            # Close dialog and navigate to Home page
            st.session_state["show_confirm_modal"] = False
            st.switch_page("pages/1_Home.py")

    with col_cancel:
        if st.button("Cancel", key="cancel_detect_log"):
            st.session_state["show_confirm_modal"] = False
            st.rerun()


def main():
    """Render the Detect page."""
    render_header(
        "Pill Detection and Counting",
        "Select a drug, review its details, then upload an image for counting.",
    )

    drugs = load_drugs()
    if not drugs:
        st.info("No drugs available. Please add drugs in the backend first.")
        return

    # Map drugs to dropdown options
    options = {f"{d.get('id')} - {d.get('trade_name', 'Unknown')}": d for d in drugs}
    drug_name_by_id = {str(d.get("id")): d.get("trade_name", "Unknown") for d in drugs}
    selected_label = st.selectbox(
        "Select drug",
        options=list(options.keys()),
    )
    selected_drug = options[selected_label]
    selected_drug_id = selected_drug.get("id")

    render_divider()

    st.subheader("Drug Information")
    col_left, col_right = st.columns([1, 2])

    with col_left:
        image_url = selected_drug.get("image")
        if image_url:
            st.image(image_url, caption=selected_drug.get("trade_name", "Drug image"))
        else:
            st.info("No reference image available for this drug.")

    with col_right:
        st.markdown(f"**Drug ID:** {selected_drug.get('id')}")
        st.markdown(f"**Trade Name:** {selected_drug.get('trade_name', '-')}")

    render_divider()

    st.subheader("Upload Image for Detection")
    uploaded = st.file_uploader(
        "Choose an image file",
        type=["jpg", "jpeg", "png"],
        help="Upload a pill image to run detection.",
    )

    result = None

    if uploaded is not None:
        st.image(uploaded, caption="Uploaded image", use_container_width=True)

        # Run detection immediately after upload, but avoid re-running
        # repeatedly on every Streamlit rerun for the same file.
        file_id = getattr(uploaded, "name", "uploaded_file")
        if hasattr(uploaded, "size"):
            file_id = f"{file_id}-{uploaded.size}"

        if (
            "last_detect_file_id" not in st.session_state
            or st.session_state["last_detect_file_id"] != file_id
        ):
            with st.spinner("Running detection..."):
                result = detect_uploaded_image(uploaded)
            st.session_state["last_detect_file_id"] = file_id
            st.session_state["last_detect_result"] = result
        else:
            result = st.session_state.get("last_detect_result")
    else:
        # Clear previous detection if no file is uploaded
        st.session_state.pop("last_detect_file_id", None)
        st.session_state.pop("last_detect_result", None)

    if result is not None:
        render_success("Detection completed.")

        render_divider()
        st.subheader("Detection Result")

        # Show counts with validation against selected drug_id
        counts = result.get("count", {})
        confidence_dict = result.get("confidence", {})
        if isinstance(counts, dict) and counts:
            # Convert keys to string for comparison because API keys may be stringified
            selected_id_str = (
                str(selected_drug_id) if selected_drug_id is not None else None
            )

            # Split counts into matched and mismatched groups
            matched_counts = {}
            mismatched_counts = {}

            for label_key, detected_count in counts.items():
                label_str = str(label_key)
                if selected_id_str is not None and label_str == selected_id_str:
                    matched_counts[label_str] = detected_count
                else:
                    mismatched_counts[label_str] = detected_count

            # Show matched counts (same key as selected drug_id)
            if matched_counts:
                st.markdown("**Detected pill counts (matched selected drug):**")
                for label_str, detected_count in matched_counts.items():
                    trade_name = drug_name_by_id.get(
                        label_str, f"Unknown (label {label_str})"
                    )
                    # Get confidence value (convert to percentage)
                    conf_value = confidence_dict.get(label_str) or confidence_dict.get(
                        int(label_str)
                    )
                    st.markdown(f"##### {trade_name}")
                    st.markdown(f"- **Amount:** {detected_count} pill(s)")
                    st.markdown(
                        f"- **Average confidence:** "
                        f"{f'{conf_value * 100:.2f}%' if conf_value is not None else 'N/A'}"
                    )

            # Show mismatched counts (different key from selected drug_id)
            if mismatched_counts:
                st.error(
                    "Detected pill label(s) do not match the selected drug ID. "
                    "Please review the results carefully."
                )
                st.markdown("**Detected pill counts (other drugs):**")
                for label_str, detected_count in mismatched_counts.items():
                    trade_name = drug_name_by_id.get(
                        label_str, f"Unknown (label {label_str})"
                    )
                    # Get confidence value (convert to percentage)
                    conf_value = confidence_dict.get(label_str) or confidence_dict.get(
                        int(label_str)
                    )
                    st.markdown(f"##### {trade_name}")
                    st.markdown(f"- **Amount:** {detected_count} pill(s)")
                    st.markdown(
                        f"- **Average confidence:** "
                        f"{f'{conf_value * 100:.2f}%' if conf_value is not None else 'N/A'}"
                    )

            # Confirmation button and modal to create log & update inventory
            matched_total = 0
            matched_confidence_value = None
            if matched_counts:
                # There should typically be at most one matched label (selected drug)
                # but we sum in case of future expansion.
                for label_str, detected_count in matched_counts.items():
                    matched_total += detected_count
                    if matched_confidence_value is None:
                        matched_confidence_value = confidence_dict.get(
                            label_str
                        ) or confidence_dict.get(int(label_str))

            if matched_total > 0:
                render_divider()
                st.subheader("Confirm pill counting")

                if "show_confirm_modal" not in st.session_state:
                    st.session_state["show_confirm_modal"] = False

                if st.button("Confirm and update inventory", type="primary"):
                    st.session_state["show_confirm_modal"] = True

                if st.session_state.get("show_confirm_modal"):
                    confirm_pill_dialog(
                        selected_drug=selected_drug,
                        selected_drug_id=selected_drug_id,
                        matched_total=matched_total,
                        matched_confidence_value=matched_confidence_value,
                    )

        else:
            st.info("No pills detected in the image.")

        # Show annotated image from base64
        annotated_base64 = result.get("annotated_image_base64")
        if annotated_base64:
            try:
                annotated_image = base64_to_image(annotated_base64, return_format="PIL")
                st.image(
                    annotated_image,
                    caption="Annotated detection result",
                    use_container_width=True,
                )
            except Exception as exc:
                render_error(f"Failed to render annotated image: {exc}")


if __name__ == "__main__":
    main()
