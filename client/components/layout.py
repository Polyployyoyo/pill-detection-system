import streamlit as st


def render_header(title: str, subtitle: str | None = None) -> None:
    """
    Render a shared page header.

    Args:
        title: Main page title text.
        subtitle: Optional subtitle/description text.
    """
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def render_divider() -> None:
    """Render a visual divider between sections."""
    st.markdown("---")


def render_error(message: str) -> None:
    """
    Render a standard error message.

    Args:
        message: Error text to display.
    """
    st.error(message)


def render_success(message: str) -> None:
    """
    Render a standard success message.

    Args:
        message: Success text to display.
    """
    st.success(message)

