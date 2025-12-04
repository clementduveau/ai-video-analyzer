import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

st.set_page_config(page_title="Documentation", page_icon="📚")

st.title("📚 Documentation")
st.write("Access the project documentation below:")

st.page_link("https://github.com/dsmilne3/ai-video-analyzer", label="📖 Open Documentation", icon="🔗")