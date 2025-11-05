# Demo Video Analyzer

Automatically evaluate demo videos using AI. This project implements a **local-first pipeline** with optional cloud API escalation for cost optimization.

## Features

✅ **Implemented (High-Priority Capabilities)**

- ✓ ASR transcription with timestamps using Whisper (local, free)
- ✓ **Transcription quality metrics** (confidence, speech detection, compression ratio)
- ✓ **Automatic language detection** (Whisper detects 99+ languages)
- ✓ **Translation to English** (optional Whisper-based translation for non-English demos)
- ✓ Auto-summary and jump-to highlights
- ✓ **Multiple evaluation rubrics** (sales-demo, technical-demo, default)
- ✓ **Qualitative feedback generation with 2 strengths and 2 areas for improvement**
- ✓ **Adaptive tone (congratulatory for passing scores, supportive for failing scores)**
- ✓ Multimodal alignment checks (non-feature-specific) between transcript and video frames
- ✓ Support for multiple video formats (MP4, MOV, AVI, MKV) and audio formats (MP3, WAV, M4A, AAC)
- ✓ **URL support** (YouTube, Vimeo, and direct video links)
- ✓ **Auto-save results with timestamps** (no overwrites)
- ✓ **CLI pagination** (results displayed through `less`/`more`)
- ✓ **Progress reporting** in UI terminal during analysis
- ✓ Choose between OpenAI or Anthropic models for evaluation
- ✓ CLI tool for batch processing
- ✓ Streamlit reviewer app with file upload and URL input

## Architecture

**Recommended Default: Local-First with Escalation**

- Primary: Local Whisper transcription + heuristic evaluation (free, privacy-preserving)
- Escalation: Call paid APIs (OpenAI/Anthropic) only for low-confidence transcripts or human-flagged videos
- Vision analysis: Optional multimodal alignment checks for transcript verification

## Quick Start

### 0. Check Dependencies (Recommended First Step)

```bash
# Check if all dependencies are installed
python3 check_dependencies.py
```

This will show you which dependencies are installed and which are missing.

### 1. Install System Dependencies

```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Linux (RHEL/CentOS)
sudo yum install ffmpeg
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python check_dependencies.py
```

### 3. Set API Keys (Optional)

For full LLM evaluation (not needed for basic testing):

```bash
export API_KEY=your-openai-or-anthropic-api-key
```

### 4. Run Demo

```bash
# List available rubrics
python cli/evaluate_video.py --list-rubrics

# Test with pre-generated realistic audio (~90 seconds of actual product demo)
# This file is included in the repo and ready to use!
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai

# Use a specific rubric (sales-demo, technical-demo, or default)
python cli/evaluate_video.py test_data/realistic_demo.wav --rubric sales-demo --provider openai

# Or test end-to-end without requiring real audio/video
python test_data/run_end_to_end_demo.py

# Evaluate a real video file (requires ffmpeg + API key)
python cli/evaluate_video.py path/to/demo.mp4 --provider anthropic

# Evaluate a video from URL (YouTube, Vimeo, or direct links)
python cli/evaluate_video.py "https://youtube.com/watch?v=..." --provider openai

# Keep original language (disable translation)
python cli/evaluate_video.py spanish_demo.mp4 --provider openai --no-translate

# With vision analysis
python cli/evaluate_video.py path/to/demo.mp4 --provider openai --vision

# Launch reviewer UI (with rubric selector, file upload, and URL input)
streamlit run app/reviewer.py
```

**Note**: The `realistic_demo.wav` file contains synthetic speech simulating a real product demo (pre-generated and included in the repo). See `test_data/realistic_demo_script.md` and `test_data/realistic_demo_transcript.md` for the script and transcription.

## Evaluation Rubrics

The system supports **multiple evaluation rubrics** for different types of demos. Each rubric defines criteria, weights, and thresholds optimized for specific use cases (e.g., sales demos, technical demos, general partner demos).

### Using Rubrics

```bash
# List all available rubrics
python cli/evaluate_video.py --list-rubrics

# Use a specific rubric
python cli/evaluate_video.py video.mp4 --rubric sales-demo --provider openai

# Use default rubric (if --rubric not specified)
python cli/evaluate_video.py video.mp4 --provider openai
```

The `--list-rubrics` command shows all available rubrics with their descriptions and criteria.

### Creating Custom Rubrics

You can create custom rubrics by adding JSON files to the `rubrics/` directory. See `rubrics/README.md` for:

- Rubric structure and requirements
- Examples of existing rubrics
- Instructions for creating custom rubrics
- Validation rules

## Language Support & Translation

The system supports **99+ languages** through Whisper's automatic language detection:

### Automatic Language Detection

Whisper automatically detects the language of the audio and displays it in both the CLI and UI:

- **CLI**: Shows "Detected Language: ES" (or other ISO code)
- **UI**: Displays in the Transcription Quality expander

### Translation to English (Default)

**Translation is enabled by default** to ensure consistent English evaluations across all demos.

**CLI:**

```bash
# Translation enabled by default (no flag needed)
python cli/evaluate_video.py spanish_demo.mp4 --provider openai

# Disable translation to keep original language
python cli/evaluate_video.py french_demo.wav --provider openai --no-translate
```

**UI:**

- "Translate to English" is checked by default
- Uncheck to keep the original language

**How it works:**

- Uses Whisper's built-in translation capability
- Free, local translation (no API costs)
- High quality (same model used by professionals)
- Maintains technical term accuracy

**When detected language is translated:**

- Shows: "Detected Language: ES → 🌐 Translated to English"
- Evaluation and feedback use the English translation

**Supported languages:** All languages Whisper supports (99+), including:

- Spanish, French, German, Italian, Portuguese
- Japanese, Chinese, Korean
- Arabic, Russian, Dutch, Polish
- And many more...

**Future enhancements:** See `REMINDER_TRANSLATION_OPTIONS.md` for additional translation capabilities (translate to languages other than English, multi-language feedback, etc.)

## Results Storage

After each evaluation, results are **automatically saved** to the `results/` folder with timestamps to preserve evaluation history:

### CLI Results

- **Format**: Human-readable text file with full transcript and JSON
- **Location**: `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
- **Contents**:
  - Evaluation summary (status, score, summary)
  - Transcription quality metrics
  - Detailed feedback (strengths & improvements)
  - Full transcript
  - Complete JSON output

### UI Results

- **Format**: Human-readable text file
- **Location**: `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
- **Download**: Interactive download button in the UI
- **Contents**: Same as CLI (evaluation summary, quality metrics, feedback, transcript)

**Note**: JSON export is currently disabled for UI simplicity. See `REMINDER_JSON_EXPORT.md` if you need structured data export for dashboards, APIs, or bulk analysis.

### No Overwrites

Each evaluation creates a **new timestamped file**, so you can:

- Compare results across multiple runs
- Track improvements over time
- Preserve complete evaluation history
- Never lose previous results

**Example**:

```bash
# After running evaluation
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai

# Results saved with timestamp
# Output: 💾 Results saved to: results/realistic_demo_results_20251010_130222.txt

# Run again - creates a new file instead of overwriting
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai
# Output: 💾 Results saved to: results/realistic_demo_results_20251010_143015.txt

# View all results for this file
ls results/realistic_demo_results_*.txt
```

The `results/` directory is git-ignored to avoid committing evaluation outputs.

## Feedback for Submitters

In addition to numeric scores, the evaluator generates **qualitative feedback** for each video:

- **2 Strengths**: Specific areas where the demo excelled (2-3 sentences each)
- **2 Areas for Improvement**: Actionable suggestions for enhancement (2-3 sentences each)
- **Adaptive Tone**:
  - **Congratulatory** tone for passing videos (score ≥ 6.5)
  - **Supportive** tone for videos needing revision (score < 6.5)

This feedback is designed to help submitters understand their performance and improve future demos.

## Project Structure

```
demo-video-analyzer/
├── src/
│   └── video_evaluator.py    # Core evaluator with rubric logic
├── cli/
│   └── evaluate_video.py     # Command-line interface
├── app/
│   └── reviewer.py           # Streamlit reviewer UI
├── rubrics/
│   ├── default.json          # Default rubric for general demos
│   ├── sales-demo.json       # Sales-focused rubric
│   ├── technical-demo.json   # Technical deep-dive rubric
│   └── README.md             # Rubric documentation
├── results/                  # Auto-saved evaluation results (git-ignored)
│   └── .gitignore            # Keeps results private
├── tests/
│   └── test_evaluator.py     # Unit tests
├── test_data/
│   ├── realistic_demo.wav              # Pre-generated test audio (included)
│   ├── realistic_demo_script.md        # Original demo script
│   ├── realistic_demo_transcript.md    # Whisper transcription
│   ├── realistic_demo_transcript.txt   # Plain text transcript
│   ├── run_end_to_end_demo.py          # End-to-end testing script
│   └── README.md                       # Test data documentation
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Cost Optimization

**Free/Local Components:**

- Whisper (transcription): Open-source, runs locally
- ffmpeg: Free audio/video processing
- OpenCV: Free frame extraction
- Streamlit: Free UI framework

**Paid/Cloud Components (Optional):**

- OpenAI GPT-4o: ~$2.50 per 1M input tokens, $10 per 1M output tokens
- Anthropic Claude: ~$3 per 1M input tokens, $15 per 1M output tokens
- Vision APIs: ~$0.01-0.05 per image

**Recommended Strategy:**

1. Process all videos locally with Whisper (free)
2. Use fallback heuristic scoring (free)
3. Only call paid LLM APIs for:
   - Low-confidence transcripts (< 80% average confidence)
   - Human-flagged videos requiring deeper analysis
   - Final review/top submissions

## Next Steps

**Ready to Implement:**

- [ ] Add escalation hook (auto-route to paid APIs based on confidence thresholds)
- [ ] Integrate AssemblyAI/Deepgram for production-grade ASR with diarization
- [ ] Add PII detection and redaction
- [ ] Implement batch processing queue
- [ ] Add cost estimator and usage tracking
- [ ] Build calibration dataset for model tuning

## Testing

```bash
# Run unit tests
pytest -q

# Run end-to-end demo
python test_data/run_end_to_end_demo.py
```

## Documentation

Additional documentation is available in the `docs/` folder:

- **Feature Documentation:**

  - `FEEDBACK_FEATURE.md` - Qualitative feedback generation
  - `MULTI_RUBRIC_FEATURE.md` - Multiple rubric support
  - `RESULTS_FEATURE.md` - Results saving and export
  - `TIMESTAMP_FEATURE.md` - Timestamped results implementation
  - `TRANSCRIPTION_QUALITY.md` - Transcription quality metrics

- **Implementation Details:**

  - `IMPLEMENTATION_SUMMARY.md` - Overall architecture summary
  - `QUALITATIVE_FEEDBACK_SUMMARY.md` - Feedback system details
  - `VERIFICATION_RESULTS.md` - Testing and validation

- **Setup Guides:**

  - `API_KEYS.md` - API key configuration
  - `DEPENDENCY_CHECKER.md` - Dependency verification
  - `RESULTS_QUICKSTART.md` - Quick start for results feature

- **Examples:**

  - `FEEDBACK_EXAMPLE.md` - Sample feedback outputs
  - `REALISTIC_TEST_AUDIO.md` - Test data information

- **Behavior Notes:**

  - `STREAMLIT_BEHAVIOR.md` - Streamlit UI behavior notes

- **Reminders:**
  - `REMINDER_JSON_EXPORT.md` - JSON export feature (currently disabled)
  - `REMINDER_RUBRIC_HELPER.md` - Rubric helper script idea

## Requirements

- Python 3.9+
- ffmpeg (for audio/video processing)
- 2GB+ RAM (for Whisper base model)
- Optional: GPU for faster transcription

## License

See LICENSE file for details.
