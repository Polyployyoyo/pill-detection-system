import streamlit as st


def main() -> None:
    """
    Entry point for the Streamlit application.

    Streamlit will automatically discover additional pages from the `pages`
    directory. This main file serves as a simple landing page.
    """
    st.set_page_config(
        page_title="Pill Detection System",
        layout="wide",
    )

    st.title("Pill Detection System")
    st.markdown(
        "Use the navigation sidebar to access all available modules: **Inventory**, **Detect**, **Add Inventory**, **Move Inventory**, and **History**."
    )


if __name__ == "__main__":
    main()
