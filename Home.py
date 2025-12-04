import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="AI-Assisted Demo Video Grading - AI Video Analyzer",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI-Assisted Demo Video Grading")
st.markdown("""
    Welcome to the AI Video Analyzer - your intelligent assistant for evaluating demo videos.  
      
    Leveraging AI technology to automatically analyze demo videos with precision and consistency and generate  
    consistent, objective feedback for submitters will transform your video evaluation process.
    """)

# Key features
st.markdown("---")
st.subheader("✨ Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🎯 **AI-Powered Analysis**
    - Automatic translation using Whisper
    - Intelligent rubric-based evaluation
    - Consistent scoring across evaluators
    - Detailed qualitative feedback
    """)

with col2:
    st.markdown("""
    ### 📊 **Comprehensive Rubrics**
    - Hierarchical evaluation criteria
    - Customizable scoring systems
    - Version control and management
    - Import/export capabilities
    """)

with col3:
    st.markdown("""
    ### 🎬 **Video Processing**
    - Support for multiple formats (MP4, MOV, AVI, MKV)
    - URL-based video analysis
    - Progress tracking and timestamps
    - Quality metrics and insights
    """)

# Getting started section
st.markdown("---")
st.subheader("🎯 Getting Started")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📊 Manage Rubrics")
    st.markdown("Create, edit, and organize your evaluation rubrics.")
    if st.button("📊 Open Rubric Dashboard", use_container_width=True, type="secondary"):
        st.switch_page("pages/3_View_or_Edit_Rubric.py")

with col2:
    st.markdown("### 🎬 Analyze Videos")
    st.markdown("Upload videos and get AI-powered evaluations.")
    if st.button("🎬 Analyze Videos", use_container_width=True, type="primary"):
        st.switch_page("pages/2_Analyze_Video.py")

with col3:
    st.markdown("### 📚 Learn More")
    st.markdown("Explore documentation and examples.")
    st.markdown("[📚 View Documentation](https://github.com/dsmilne3/ai-video-analyzer)")

# Recent activity / stats
st.markdown("---")
st.subheader("📈 System Overview")

# Get some basic stats
try:
    from rubric_helper import list_available_rubrics, get_rubrics_dir
    available_rubrics = list_available_rubrics()
    rubrics_dir = get_rubrics_dir()
    total_files = len(list(rubrics_dir.glob("*.json"))) + len(list((rubrics_dir / "versions").glob("*.json"))) if (rubrics_dir / "versions").exists() else 0

    col1, col2, col3 = st.columns(3)
    # Check if analysis results directory exists and count files
    results_dir = Path(__file__).parent / "results"
    result_count = len(list(results_dir.glob("*.json"))) if results_dir.exists() else 0
    # Calculate sample vs customized rubrics
    sample_rubrics = [r for r in available_rubrics if r['filename'].startswith('sample')]
    customized_count = len(available_rubrics) - len(sample_rubrics)
    with col1:
        st.metric("Completed Analyses", result_count)
    with col2:
        st.metric("Customized Rubrics", customized_count)
    with col3:
        st.metric("Sample Rubrics", len(sample_rubrics))

except Exception as e:
    st.info("System stats will be available once you start using the application.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
        AI Video Analyzer - Powered by OpenAI, Anthropic, and Whisper<br>
        Built with Streamlit • Local-first architecture for privacy
    </small>
</div>
""", unsafe_allow_html=True)

# Version info
try:
    from importlib.metadata import version
    streamlit_version = version('streamlit')
    st.caption(f"Streamlit v{streamlit_version}")
except ImportError:
    # Fallback for older Python versions
    try:
        import pkg_resources
        streamlit_version = pkg_resources.get_distribution("streamlit").version
        st.caption(f"Streamlit v{streamlit_version}")
    except:
        pass