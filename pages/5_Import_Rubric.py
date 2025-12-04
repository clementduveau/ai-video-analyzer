import sys
import os
import requests
import json
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from pathlib import Path
from validation_ui import validate_and_display
from rubric_helper import (
    list_available_rubrics, save_rubric_to_file, validate_rubric
)

st.set_page_config(
    page_title="📥 Import Rubric - AI Video Analyzer",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Import Rubric")
st.markdown("Import evaluation rubrics from JSON files. Supports both local files and URLs.")

# Import method selection
import_method = st.radio(
    "",
    ["Upload Local File", "Import from URL"],
    horizontal=True
)

rubric_data = None
import_error = None
source_info = ""

if import_method == "Upload Local File":
    st.markdown("#### 📁 Select Local File")
    uploaded_file = st.file_uploader(
        "",
        type=["json"],
        help="Upload a rubric JSON file from your computer"
    )

    if uploaded_file is not None:
        try:
            rubric_data = json.load(uploaded_file)
            source_info = f"Local file: {uploaded_file.name}"
        except json.JSONDecodeError as e:
            import_error = f"Invalid JSON file: {e}"
        except Exception as e:
            import_error = f"Error reading file: {e}"

elif import_method == "Import from URL":
    st.markdown("##### 🌐 Import from URL")
    url = st.text_input(
        "",
        placeholder="https://example.com/rubric.json",
        help="Enter the URL of a publicly accessible rubric JSON file"
    )

    if url and st.button("🔍 Fetch Rubric", use_container_width=False):
        if not url.startswith(('http://', 'https://')):
            import_error = "URL must start with http:// or https://"
        else:
            try:
                with st.spinner("Fetching rubric from URL..."):
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    rubric_data = response.json()
                    source_info = f"URL: {url}"
            except requests.exceptions.RequestException as e:
                import_error = f"Error fetching URL: {e}"
            except json.JSONDecodeError as e:
                import_error = f"Invalid JSON from URL: {e}"
            except Exception as e:
                import_error = f"Unexpected error: {e}"

# Display import results
if import_error:
    st.error(f"❌ Import failed: {import_error}")
elif rubric_data:
    st.success("✅ Rubric imported successfully!")
    st.info(f"**Source:** {source_info}")

    # Display basic rubric info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Name:** {rubric_data.get('name', 'Unknown')}")
    with col2:
        st.metric("Version", rubric_data.get('version', 'N/A'))
    with col3:
        format_type = "Hierarchical" if "categories" in rubric_data else "Legacy"
        st.metric("Format", format_type)

    # Validate the imported rubric
    st.markdown("### 🔍 Validation")
    is_valid = validate_and_display(rubric_data, rubric_data.get('name', 'Imported Rubric'), mode="full")

    if is_valid:
        # Import options
        st.markdown("### 💾 Import Options")

        # Generate suggested filename
        rubric_name = rubric_data.get('name', 'imported_rubric')
        suggested_filename = rubric_name.lower().replace(' ', '_').replace('-', '_')
        suggested_filename = ''.join(c for c in suggested_filename if c.isalnum() or c == '_')

        # Check for existing rubrics
        existing_rubrics = list_available_rubrics()
        existing_names = [r['filename'] for r in existing_rubrics]

        col1, col2 = st.columns([2, 1])
        with col1:
            filename = st.text_input(
                "Filename",
                value=suggested_filename,
                help="Choose a unique filename for this rubric"
            )
        with col2:
            overwrite = st.checkbox(
                "Overwrite if exists",
                help="Replace existing rubric with same filename"
            )

        # Check filename validity
        filename_valid = True
        filename_error = ""

        if not filename.strip():
            filename_valid = False
            filename_error = "Filename cannot be empty"
        elif filename in existing_names and not overwrite:
            filename_valid = False
            filename_error = "Filename already exists. Check 'Overwrite' to replace it."
        elif not filename.replace('_', '').replace('-', '').isalnum():
            filename_valid = False
            filename_error = "Filename can only contain letters, numbers, underscores, and hyphens"

        if filename_error:
            st.error(f"❌ {filename_error}")

        # Import button
        if st.button("📥 Import Rubric", use_container_width=True, type="primary", disabled=not filename_valid):
            success, error = save_rubric_to_file(rubric_data, filename, create_backup=overwrite)
            if success:
                st.success(f"✅ Rubric '{rubric_data.get('name', filename)}' imported successfully!")
                st.info(f"**Filename:** {filename}.json")
                st.info("Switch to the **'📋 View Rubrics'** page to see your imported rubric.")
                # Store import success info in session state for auto-selection
                st.session_state['auto_select_rubric'] = filename
                if st.button("📋 View Imported Rubric", key="view_imported"):
                    # Keep auto_select_rubric for auto-selection in target page
                    st.switch_page("pages/3_View_or_Edit_Rubric.py")
                st.balloons()
            else:
                st.error(f"❌ Error importing rubric: {error}")
    else:
        st.warning("⚠️ The imported rubric has validation errors. You can still import it, but it may not work correctly with the evaluation system.")

# Help section
with st.expander("ℹ️ Import Help"):
    st.markdown("""
    **Supported Rubric Formats:**

    **Hierarchical Format (Recommended):**
    ```json
    {
      "name": "My Rubric",
      "version": "1.0",
      "categories": [
        {
          "category_id": "content_quality",
          "label": "Content Quality",
          "weight": 0.6,
          "max_points": 30,
          "criteria": [...]
        }
      ],
      "scale": {"min": 0, "max": 50},
      "thresholds": {"pass": 35, "revise": 25}
    }
    ```

    **Legacy Format (Flat Criteria):**
    ```json
    {
      "name": "Legacy Rubric",
      "criteria": [...],
      "scale": {"min": 0, "max": 10},
      "thresholds": {"pass": 7, "revise": 5}
    }
    ```

    **Import Methods:**
    - **Local File:** Upload a JSON file from your computer
    - **URL:** Provide a link to a publicly accessible JSON file

    **Tips:**
    - Filenames should be unique and contain only letters, numbers, underscores, and hyphens
    - Imported rubrics are automatically validated
    - You can overwrite existing rubrics by checking the overwrite option
    """)

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📋 View/Edit Rubrics", use_container_width=True):
        # Keep auto_select_rubric for auto-selection in target page
        st.switch_page("pages/3_View_or_Edit_Rubric.py")
with col2:
    if st.button("➕ Create Rubric", use_container_width=True):
        st.switch_page("pages/4_Create_Rubric.py")
with col3:
    if st.button("📚 Manage Versions", use_container_width=True):
        # Keep auto_select_rubric for auto-selection in target page
        st.switch_page("pages/7_Manage_Rubrics.py")