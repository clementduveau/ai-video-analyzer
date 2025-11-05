import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables explicitly
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import streamlit as st
import json
from pathlib import Path

# Check for dependencies
try:
    from src.video_evaluator import VideoEvaluator, AIProvider, list_available_rubrics, save_results
except ImportError as e:
    st.error("❌ Missing dependencies!")
    st.write(f"Error: {e}")
    st.write("")
    st.write("To check which dependencies are missing, run:")
    st.code("python check_dependencies.py", language="bash")
    st.write("To install all dependencies:")
    st.code("pip install -r requirements.txt", language="bash")
    st.stop()

st.title('Demo Video Reviewer')

# Add dependency check status in sidebar
with st.sidebar:
    st.subheader("System Status")
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Check OpenAI key
    if openai_key and openai_key.startswith('sk-') and not openai_key.endswith('your-openai-key-here'):
        st.success("✓ OpenAI API key loaded")
    else:
        st.error("❌ OpenAI API key missing or invalid")
    
    # Check Anthropic key
    if anthropic_key and anthropic_key.startswith('sk-ant-') and not anthropic_key.endswith('your-anthropic-key-here'):
        st.success("✓ Anthropic API key loaded")
    else:
        st.warning("⚠️ Anthropic API key missing or invalid (optional)")
    
    # Quick check for ffmpeg
    import subprocess
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            st.success("✓ ffmpeg installed")
        else:
            st.error("❌ ffmpeg not found")
            st.caption("Install with: brew install ffmpeg")
    except:
        st.warning("⚠️ Could not check ffmpeg")
    
    st.caption("Run `python check_dependencies.py` for full system check")

# Submitter information - moved to top
st.subheader("👤 Submitter Information")
col1, col2 = st.columns(2)
with col1:
    first_name = st.text_input("First Name", placeholder="Enter first name")
with col2:
    last_name = st.text_input("Last Name", placeholder="Enter last name")

partner_name = st.text_input("Partner Name", placeholder="Enter partner name (e.g. AHEAD, Bynet, WWT etc.)")

# Initialize session state for tracking uploaded file and URL
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'video_url' not in st.session_state:
    st.session_state.video_url = ''

# Input method selection
input_method = st.radio(
    "Input Method",
    ["Upload File", "URL"],
    horizontal=True
)

if input_method == "Upload File":
    # File upload - use disabled parameter to truly prevent clicking
    if st.session_state.uploaded_file is None:
        # No file uploaded - show enabled uploader
        uploaded = st.file_uploader(
            'Upload a local video or audio file', 
            type=['mp4','mov','mkv','avi','mp3','wav','m4a'],
            key='file_uploader_enabled'
        )
        if uploaded:
            st.session_state.uploaded_file = uploaded
            st.session_state.video_url = ''  # Clear URL when file uploaded
            st.rerun()
    else:
        # File already uploaded - show disabled uploader that displays the file
        st.file_uploader(
            'Upload a local video or audio file', 
            type=['mp4','mov','mkv','avi','mp3','wav','m4a'],
            disabled=True,
            key='file_uploader_disabled'
        )
        # Show the stored file with option to clear
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"📄 {st.session_state.uploaded_file.name}")
        with col2:
            if st.button("✕", key="clear_file", help="Remove file"):
                st.session_state.uploaded_file = None
                st.rerun()
else:
    # URL input
    video_url = st.text_input(
        'Video URL',
        value=st.session_state.video_url,
        placeholder='',
        label_visibility='collapsed'
    )
    
    if video_url != st.session_state.video_url:
        st.session_state.video_url = video_url
        st.session_state.uploaded_file = None  # Clear file when URL entered
    
    if st.session_state.video_url:
        # Validate URL format
        from urllib.parse import urlparse
        try:
            parsed = urlparse(st.session_state.video_url)
            is_valid_url = all([parsed.scheme in ['http', 'https'], parsed.netloc])
        except:
            is_valid_url = False
        
        if not is_valid_url:
            st.error("⚠️ Invalid URL format. Please enter a valid http:// or https:// URL.")
        else:
            # Only show the URL box and clear button if valid
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"🔗 {st.session_state.video_url}")
            with col2:
                if st.button("✕", key="clear_url", help="Remove URL"):
                    st.session_state.video_url = ''
                    st.rerun()

# Get available rubrics
available_rubrics = list_available_rubrics()
rubric_options = {r['name']: r['filename'] for r in available_rubrics}
rubric_descriptions = {r['name']: r['description'] for r in available_rubrics}

# Rubric selection
selected_rubric_name = st.selectbox(
    'Evaluation Rubric',
    options=list(rubric_options.keys()),
    help='Choose the rubric to use for evaluation'
)
if selected_rubric_name:
    st.caption(f"📋 {rubric_descriptions[selected_rubric_name]}")

provider = st.selectbox('AI Provider', ['openai','anthropic'])
translate = st.checkbox('Translate to English', value=True, help='Automatically translate non-English audio to English using Whisper')
vision = st.checkbox('Enable visual alignment checks')

# Use the file from session state
uploaded = st.session_state.uploaded_file
video_url = st.session_state.video_url

# Validate URL if provided
from urllib.parse import urlparse
url_is_valid = True
if video_url and video_url.strip():
    try:
        parsed = urlparse(video_url)
        url_is_valid = all([parsed.scheme in ['http', 'https'], parsed.netloc])
    except:
        url_is_valid = False

# Enable analyze button if either file or valid URL is provided AND required fields are filled
can_analyze = (uploaded is not None or (video_url and video_url.strip() and url_is_valid)) and first_name.strip() and last_name.strip() and partner_name.strip()

if st.button("🚀 Analyze Video", disabled=not can_analyze, use_container_width=True):
    # Warn user about UI unresponsiveness
    warning_placeholder = st.empty()
    warning_placeholder.warning("⚠️ **Analysis in progress** - The interface may be slow or unresponsive during processing. This is normal and can take several minutes depending on video length and model used for transcription/translation.")
    
    tmp = None
    try:
        prov = AIProvider.OPENAI if provider == 'openai' else AIProvider.ANTHROPIC
        rubric_filename = rubric_options[selected_rubric_name]
        
        # Progress callback that prints to terminal (stdout)
        def progress_callback(message: str):
            print(message, flush=True)
        
        # Show progress with status updates
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Progress callback that updates the UI in real-time
        def ui_progress_callback(message: str):
            # Map internal progress messages to UI step numbers
            if "Downloading from URL" in message:
                progress_placeholder.write("⏳ **Step 1/4:** Downloading video/audio...")
            elif "Download complete" in message:
                progress_placeholder.write("⏳ **Step 2/4:** Transcribing audio with Whisper...")
            elif "Transcribing audio" in message:
                # Extract model name from message like "🎤 Transcribing audio with Whisper base model..."
                if "Whisper" in message and "model" in message:
                    progress_placeholder.write(f"⏳ **Step 2/4:** {message.replace('🎤 ', '')}")
                else:
                    progress_placeholder.write("⏳ **Step 2/4:** Transcribing audio with Whisper base model...")
            elif "Analyzing video frames" in message:
                progress_placeholder.write("⏳ **Step 3/4:** Analyzing video frames...")
            elif "Evaluating transcript" in message:
                progress_placeholder.write("⏳ **Step 3/4:** Evaluating with AI...")
            elif "Generating qualitative feedback" in message:
                progress_placeholder.write("⏳ **Step 4/4:** Generating feedback...")
            # Also print to terminal for debugging
            print(message, flush=True)
        
        evaluator = VideoEvaluator(
            provider=prov, 
            enable_vision=vision, 
            rubric_path=rubric_filename, 
            verbose=False,  # Back to normal - warnings now shown in UI
            progress_callback=ui_progress_callback,
            translate_to_english=translate
        )
        
        with status_placeholder.container():
            progress_placeholder.write("⏳ **Step 1/4:** Preparing audio...")
            progress_placeholder.caption("This may take a few minutes, depending on audio/video length")
            
            # Process based on input type
            if uploaded:
                # File upload - save to temp
                tmp = f"/tmp/{uploaded.name}"
                with open(tmp, 'wb') as f:
                    f.write(uploaded.getbuffer())
                res = evaluator.process(tmp, is_url=False, enable_vision=vision)
                original_filename = uploaded.name
            else:
                # URL - process directly
                res = evaluator.process(video_url, is_url=True, enable_vision=vision)
                # Extract filename from URL for results saving
                from urllib.parse import urlparse
                import os
                parsed_url = urlparse(video_url)
                original_filename = os.path.basename(parsed_url.path) or "video_from_url"
            
            # Print completion to terminal
            print("✅ Analysis complete!", flush=True)
            print("", flush=True)
            print("", flush=True)
        
        # Add submitter information to results
        res['submitter'] = {
            'first_name': first_name.strip(),
            'last_name': last_name.strip(),
            'partner_name': partner_name.strip()
        }
        
        progress_placeholder.empty()
        status_placeholder.empty()
        
        # Clear the warning message now that analysis is complete
        warning_placeholder.empty()

        # Display transcription quality first (for reviewer confidence)
        quality = res.get('quality', {})
        if quality:
            quality_rating = quality.get('quality_rating', 'unknown').upper()
            
            with st.expander(f"🎤 Transcription Quality: {quality_rating}", expanded=False):
                # Check if transcription failed
                transcript_text = res.get('transcript', '')
                if transcript_text == "(mock) transcribed text from audio":
                    st.error("❌ **Transcription failed** - Whisper model could not load. Using mock transcript.")
                    st.caption("This usually happens due to memory constraints or missing dependencies.")
                
                # Display detected language
                language = res.get('language', 'unknown')
                if translate and language.lower() != 'en':
                    st.write(f"**Detected Language:** {language.upper()} → 🌐 Translated to English")
                    st.caption("Audio was translated to English by Whisper during transcription")
                else:
                    st.write(f"**Detected Language:** {language.upper()}")
                    st.caption("Language automatically detected by Whisper during transcription")
                
                warnings = quality.get('warnings', [])
                if warnings:
                    st.warning("⚠️ **Quality Warnings:**")
                    for warning in warnings:
                        st.write(f"  - {warning}")
                
                st.write(f"**Confidence:** {quality.get('avg_confidence', 0):.1f}%")
                st.caption("How certain Whisper is about the transcription accuracy")
                
                st.write(f"**Speech Detection:** {quality.get('speech_percentage', 0):.1f}%")
                st.caption("Percentage of audio detected as speech vs. silence/noise")
                
                st.write(f"**Compression Ratio:** {quality.get('avg_compression_ratio', 0):.2f}")
                st.caption("Text length vs. audio duration; 1.5-2.5 is typical for normal speech")
                
                details = quality.get('details', {})
                st.write(f"**Average Log Probability:** {details.get('avg_logprob', 0):.3f}")
                st.caption("Model confidence score; values closer to 0 indicate higher confidence")
                
                st.write(f"**Segments Analyzed:** {details.get('num_segments', 0)}")
                st.caption("Number of speech segments identified in the audio")

        # Visual Analysis (if enabled) - placed right after transcription quality
        if res.get('visual_analysis'):
            visual_text = res.get('visual_analysis', '')
            # Determine if mismatches were detected
            visual_lower = visual_text.lower()
            
            # If text contains "no mismatch" or "no clear mismatch", it's clean
            # Otherwise look for problem indicators
            if 'no mismatch' in visual_lower or 'no clear mismatch' in visual_lower:
                has_mismatch = False
            else:
                # Look for actual problem indicators
                has_mismatch = any(phrase in visual_lower for phrase in [
                    'mismatch detected',
                    'does not match',
                    'not visible',
                    'inconsistent',
                    'contradiction',
                    'discrepancy'
                ])
            
            status_message = "Mismatches detected" if has_mismatch else "No mismatches detected"
            
            with st.expander(f"👁️ Visual Analysis: {status_message}", expanded=False):
                st.text(visual_text)

        # Display evaluation results prominently
        st.subheader('📊 Evaluation Results')
        evaluation = res.get('evaluation', {})
        overall = evaluation.get('overall', {})
        
        # Check if using new rubric format (has categories)
        is_new_format = 'categories' in evaluation
        
        col1, col2 = st.columns(2)
        with col1:
            if is_new_format:
                total_points = overall.get('total_points', 0)
                max_points = overall.get('max_points', 50)
                percentage = overall.get('percentage', 0)
                st.metric("Overall Score", f"{total_points}/{max_points} ({percentage:.1f}%)")
            else:
                score = overall.get('weighted_score', 0)
                st.metric("Overall Score", f"{score:.1f}/10")
        with col2:
            status = overall.get('pass_status', 'unknown').upper()
            status_color = "🟢" if status == "PASS" else ("🟡" if status == "REVISE" else "🔴")
            st.metric("Status", f"{status_color} {status}")
        
        # Display category scores for new format
        if is_new_format and 'categories' in evaluation:
            # Load the rubric to get proper labels
            rubric_filename = rubric_options[selected_rubric_name]
            rubric_path = Path(__file__).parent.parent / "rubrics" / f"{rubric_filename}.json"
            rubric_data = {}
            try:
                with open(rubric_path, 'r') as f:
                    rubric_data = json.load(f)
            except:
                pass
            
            # Create category label mapping
            category_labels = {}
            category_weights = {}
            if rubric_data and "categories" in rubric_data:
                for category in rubric_data["categories"]:
                    category_labels[category["category_id"]] = category["label"]
                    category_weights[category["category_id"]] = category.get("weight", 0)
            
            st.markdown("### 📂 Category Breakdown")
            categories = evaluation.get('categories', {})
            scores = evaluation.get('scores', {})
            
            # Create mapping of criteria to categories
            category_criteria = {}
            if rubric_data and "categories" in rubric_data:
                for category in rubric_data["categories"]:
                    category_criteria[category["category_id"]] = [
                        criterion["criterion_id"] for criterion in category["criteria"]
                    ]
            
            # Create table headers
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown("**Name**")
            with col2:
                st.markdown("**Score**")
            with col3:
                st.markdown("**Weight**")
            with col4:
                st.markdown("**Confidence**")
            
            for cat_id, cat_data in categories.items():
                cat_name = category_labels.get(cat_id, cat_id.replace('_', ' ').title())
                points = cat_data.get('points', 0)
                max_points = cat_data.get('max_points', 0)
                percentage = cat_data.get('percentage', 0)
                weight = category_weights.get(cat_id, 0)
                
                # Calculate average confidence for this category
                category_confidences = []
                if cat_id in category_criteria:
                    for criterion_id in category_criteria[cat_id]:
                        if criterion_id in scores:
                            confidence = scores[criterion_id].get('confidence')
                            if isinstance(confidence, int):
                                category_confidences.append(confidence)
                
                avg_confidence = None
                if category_confidences:
                    avg_confidence = sum(category_confidences) / len(category_confidences)
                
                # Determine confidence display
                if avg_confidence is not None:
                    if avg_confidence >= 8:
                        confidence_display = f"🟢 {avg_confidence:.1f}/10"
                    elif avg_confidence >= 6:
                        confidence_display = f"🟡 {avg_confidence:.1f}/10"
                    else:
                        confidence_display = f"🔴 {avg_confidence:.1f}/10"
                else:
                    confidence_display = "N/A"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{cat_name}**")
                with col2:
                    st.markdown(f"**{points}/{max_points}** ({percentage:.1f}%)")
                with col3:
                    st.markdown(f"**{weight:.1f}**")
                with col4:
                    st.markdown(confidence_display)
        
        # Display qualitative feedback
        feedback = res.get('feedback')
        if feedback:
            tone = feedback.get('tone', 'supportive')
            tone_emoji = "🎉" if tone == 'congratulatory' else "🤝"
            
            st.subheader(f'{tone_emoji} Feedback for Submitter')
            
            # Strengths
            st.markdown("### ✓ Strengths")
            for i, strength in enumerate(feedback.get('strengths', []), 1):
                with st.expander(f"**{strength.get('title', 'Strength')}**", expanded=True):
                    st.write(strength.get('description', ''))
            
            # Areas for improvement
            st.markdown("### → Areas for Improvement")
            for i, improvement in enumerate(feedback.get('improvements', []), 1):
                with st.expander(f"**{improvement.get('title', 'Area for improvement')}**", expanded=True):
                    st.write(improvement.get('description', ''))

        # Display detailed scores table
        scores = evaluation.get('scores', {})
        if scores:
            # Load the rubric to get proper labels
            rubric_filename = rubric_options[selected_rubric_name]
            rubric_path = Path(__file__).parent.parent / "rubrics" / f"{rubric_filename}.json"
            rubric_data = {}
            try:
                with open(rubric_path, 'r') as f:
                    rubric_data = json.load(f)
            except:
                pass
            
            # Create criterion label mapping
            criterion_labels = {}
            if rubric_data:
                if "categories" in rubric_data:
                    # New format
                    for category in rubric_data["categories"]:
                        for criterion in category["criteria"]:
                            criterion_labels[criterion["criterion_id"]] = criterion["label"]
                else:
                    # Old format
                    for criterion in rubric_data["criteria"]:
                        criterion_labels[criterion["id"]] = criterion["label"]
            
            with st.expander("### 📋 Detailed Criteria Scores", expanded=False):
                # Check if any scores are fallback (heuristic)
                fallback_criteria = []
                for criterion_id, data in scores.items():
                    note = data.get('note', '')
                    if 'Auto-generated conservative score' in note:
                        fallback_criteria.append(criterion_labels.get(criterion_id, criterion_id))
                
                if fallback_criteria:
                    st.warning(f"⚠️ **AI evaluation failed** - Using fallback scoring for: {', '.join(fallback_criteria)}")
                    st.caption("This happens when the AI API calls fail. Check your API key and network connection.")
                
                # Create table headers
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                with col1:
                    st.markdown("**Criterion**")
                with col2:
                    st.markdown("**Score**")
                with col3:
                    st.markdown("**Confidence**")
                with col4:
                    st.markdown("**Notes**")
                
                st.markdown("---")  # Divider line
                
                # Display each criterion in table format
                for criterion_id, data in scores.items():
                    criterion_name = criterion_labels.get(criterion_id, criterion_id.replace('_', ' ').title())
                    score = data.get('score', 'N/A')
                    confidence = data.get('confidence', 'N/A')
                    note = data.get('note', '')
                    
                    # Determine confidence level and color
                    if isinstance(confidence, int):
                        if confidence >= 8:
                            confidence_display = f"🟢 {confidence}/10"
                        elif confidence >= 6:
                            confidence_display = f"🟡 {confidence}/10"
                        else:
                            confidence_display = f"🔴 {confidence}/10"
                    else:
                        confidence_display = "N/A"
                    
                    # Determine max score based on rubric format
                    if is_new_format:
                        # For new format, we need to look up the max_points from the rubric
                        # Since we don't have direct access to rubric here, show score only
                        score_display = f"{score}"
                    else:
                        score_display = f"{score}/10"
                    
                    # Use columns for table-like display
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
                    with col1:
                        st.markdown(f"**{criterion_name}**")
                    with col2:
                        st.markdown(f"**{score_display}**")
                    with col3:
                        st.markdown(confidence_display)
                    with col4:
                        st.caption(note if note else "—")

        st.subheader('📝 Transcript')
        with st.expander("**View Full Transcript**", expanded=False):
            st.text(res.get('transcript', ''))

        with st.expander("**View Full JSON Results**", expanded=False):
            st.json(res)
        
        # Save results to file with new naming format
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{first_name.strip()}_{last_name.strip()}_{partner_name.strip()}_{timestamp}"
        saved_json_path = save_results(res, result_filename, output_format='json')
        
        # Show success message and provide download button
        st.success(f"💾 Results saved to `results/` folder")
        
        # Create centered download button for JSON version
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with open(saved_json_path, 'r') as f:
                json_content = f.read()
            st.download_button(
                label="📄 Download JSON Report",
                data=json_content,
                file_name=f"{result_filename}_results.json",
                mime="application/json",
                use_container_width=True
            )
    
    
    except FileNotFoundError as e:
        warning_placeholder.empty()  # Clear warning on error
        if 'ffmpeg' in str(e).lower():
            st.error("❌ ffmpeg not found")
            st.write("ffmpeg is required for video/audio processing.")
            st.write("Install with:")
            st.code("brew install ffmpeg", language="bash")
        else:
            st.error(f"File not found: {e}")
    except Exception as e:
        warning_placeholder.empty()  # Clear warning on error
        st.error(f"Error processing video: {e}")
        st.write("Run `python check_dependencies.py` to verify all dependencies are installed.")
    finally:
        # Clean up temp file
        if tmp:
            try:
                import os
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

