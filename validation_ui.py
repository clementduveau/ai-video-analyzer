#!/usr/bin/env python3
"""
Validation UI Components

Reusable Streamlit components for displaying rubric validation results.
Provides consistent validation UI across the application.
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple


def display_validation_results(
    is_valid: bool,
    error_msg: Optional[str],
    rubric_data: Optional[Dict[str, Any]] = None,
    mode: str = "inline",
    rubric_name: Optional[str] = None
) -> None:
    """
    Display validation results with consistent UI across the app.

    Args:
        is_valid: Whether the rubric passed validation
        error_msg: Error message if validation failed
        rubric_data: The rubric data (for detailed display)
        mode: Display mode - "inline", "full", or "compact"
        rubric_name: Name of the rubric being validated
    """
    if is_valid:
        _display_validation_success(rubric_data, mode, rubric_name)
    else:
        _display_validation_error(error_msg, mode, rubric_name)


def _display_validation_success(
    rubric_data: Optional[Dict[str, Any]],
    mode: str,
    rubric_name: Optional[str]
) -> None:
    """Display successful validation results."""
    if mode == "compact":
        st.success("✅ Valid")
        return

    # Success message
    if rubric_name:
        st.success(f"✅ Rubric '{rubric_name}' is valid!")
    else:
        st.success("✅ Rubric is valid!")

    if mode == "inline":
        # Minimal success display for inline usage
        return

    # Full detailed display for validation page
    st.balloons()

    if rubric_data:
        st.markdown("### Validation Results")

        # Format and status
        col1, col2 = st.columns(2)
        with col1:
            format_type = "Hierarchical (Categories)" if "categories" in rubric_data else "Legacy (Flat Criteria)"
            st.metric("Format", format_type)
        with col2:
            status = rubric_data.get('status', 'unknown')
            st.metric("Status", status.title())

        # Structure details
        if "categories" in rubric_data:
            categories = rubric_data['categories']
            st.markdown(f"**Categories:** {len(categories)}")
            st.markdown(f"**Total Criteria:** {sum(len(cat['criteria']) for cat in categories)}")
            total_weight = sum(cat.get('weight', 0) for cat in categories)
            st.markdown(f"**Total Weight:** {total_weight:.3f} (should be 1.0)")
        else:
            criteria = rubric_data.get('criteria', [])
            st.markdown(f"**Criteria:** {len(criteria)}")
            total_weight = sum(crit.get('weight', 0) for crit in criteria)
            st.markdown(f"**Total Weight:** {total_weight:.3f} (should be 1.0)")


def _display_validation_error(
    error_msg: Optional[str],
    mode: str,
    rubric_name: Optional[str]
) -> None:
    """Display validation error results."""
    if mode == "compact":
        st.error("❌ Invalid")
        return

    # Error message
    if rubric_name:
        st.error(f"❌ Rubric '{rubric_name}' is invalid:")
    else:
        st.error("❌ Rubric is invalid:")

    if error_msg:
        st.write(error_msg)

    if mode == "inline":
        # Minimal error display for inline usage
        return

    # Full detailed display for validation page
    st.markdown("### Issues Found")
    st.info("The rubric failed validation. Check the error message above for details on what needs to be fixed.")


def validate_and_display(
    rubric_data: Dict[str, Any],
    rubric_name: Optional[str] = None,
    mode: str = "inline"
) -> bool:
    """
    Validate a rubric and display results in one call.

    Args:
        rubric_data: The rubric data to validate
        rubric_name: Optional name for display
        mode: Display mode

    Returns:
        True if valid, False if invalid
    """
    from rubric_helper import validate_rubric

    is_valid, error_msg = validate_rubric(rubric_data)
    display_validation_results(is_valid, error_msg, rubric_data, mode, rubric_name)

    return is_valid
