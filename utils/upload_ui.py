from __future__ import annotations

import streamlit as st

from utils.adaptive_upload import save_uploaded_files


def render_data_upload_panel() -> None:
    with st.sidebar.expander("Upload your factory data", expanded=False):
        st.write("Upload CSV or Excel files. Column names can be different; the app will match common names automatically.")
        files = st.file_uploader("Choose files", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
        if st.button("Use uploaded data", disabled=not files):
            result = save_uploaded_files(files)
            st.session_state["active_data_dir"] = str(result["data_dir"])
            st.cache_data.clear()
            if result["imported"]:
                st.success("Imported: " + "; ".join(result["imported"]))
            if result["skipped"]:
                st.warning("Skipped: " + "; ".join(result["skipped"]))
            st.rerun()
        if st.button("Use provided sample data"):
            st.session_state.pop("active_data_dir", None)
            st.cache_data.clear()
            st.rerun()
