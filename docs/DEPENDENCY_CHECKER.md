# Dependency Checker - Implementation Summary

## What Was Added

### New File: `check_dependencies.py`

A comprehensive dependency checker that validates:

- Python version (3.9+)
- System dependencies (ffmpeg)
- Core Python packages (whisper, torch, opencv, etc.)
- Optional Python packages (openai, anthropic, streamlit, pytest)
- Supporting packages (tiktoken, numba, ffmpeg-python, etc.)
- Project structure (verifies key files exist)

### Enhanced Error Handling

**Updated Files:**

1. `cli/evaluate_video.py` - Added try/catch for imports with helpful error messages
2. `app/reviewer.py` - Added dependency check on startup + sidebar status indicator
3. `README.md` - Added dependency check as step 0 in Quick Start

## Usage

### Check All Dependencies

```bash
python check_dependencies.py
```

### Example Output - All Dependencies Present

```
======================================================================
DEMO VIDEO ANALYZER - DEPENDENCY CHECK
======================================================================

Checking system dependencies...
Checking core Python packages...
Checking optional Python packages...
Checking supporting Python packages...
Checking project structure...

======================================================================
RESULTS
======================================================================

✓ Installed components:
  ✓ Python version: 3.13.2
  ✓ ffmpeg: /opt/homebrew/bin/ffmpeg
    Version: ffmpeg version 8.0 Copyright (c) 2000-2025 the FFmpeg developers
  ✓ openai-whisper: 20250625
  ✓ torch: 2.8.0
  ✓ torchaudio: 2.8.0
  ✓ numpy: 2.2.6
  ✓ opencv-python: 4.12.0
  ... (all other packages)

✅ ALL CHECKS PASSED

The application is ready to use!

Quick start:
  python cli/evaluate_video.py path/to/demo.mp4 --provider anthropic
  streamlit run app/reviewer.py
```

### Example Output - Missing Dependencies

```
======================================================================
DEMO VIDEO ANALYZER - DEPENDENCY CHECK
======================================================================

...

======================================================================
RESULTS
======================================================================

✓ Installed components:
  ✓ Python version: 3.13.2
  ... (installed packages)

❌ ERRORS - Cannot run application:
  ❌ ffmpeg not found - required for video/audio processing
     Install with: brew install ffmpeg
  ❌ Python package 'openai-whisper' not installed

Fix the errors above and run this check again.
```

## Features

### Dependency Checker (`check_dependencies.py`)

**System Checks:**

- ✓ Python version validation (3.9+ required)
- ✓ ffmpeg installation and version detection
- ✓ Cross-platform command detection (macOS, Linux, Windows)

**Python Package Checks:**

- ✓ Core packages (required for basic functionality)
- ✓ Optional packages (needed for full features)
- ✓ Supporting packages (dependencies of core packages)
- ✓ Version detection for installed packages

**Project Structure Checks:**

- ✓ Verifies key files exist (evaluator, CLI, app, requirements.txt)
- ✓ Provides clear feedback if files are missing

**Output Categories:**

- ✓ Info: Successfully detected components
- ⚠️ Warnings: Optional components missing
- ❌ Errors: Required components missing (blocks execution)

**Exit Codes:**

- 0: All checks passed (or only optional deps missing)
- 1: Required dependencies missing

### Enhanced CLI (`cli/evaluate_video.py`)

**Import Error Handling:**

```python
try:
    from src.video_evaluator import VideoEvaluator, AIProvider
except ImportError as e:
    # Shows helpful error message with instructions
    # Suggests running check_dependencies.py
    sys.exit(1)
```

**Runtime Error Handling:**

- Catches ffmpeg not found errors
- Provides installation instructions
- Always suggests running dependency checker

**Help Text:**

- Added epilog suggesting dependency check command

### Enhanced Streamlit App (`app/reviewer.py`)

**Startup Check:**

- Catches import errors immediately
- Shows error in Streamlit UI with instructions
- Stops app launch if dependencies missing

**Sidebar Status Indicator:**

- Quick check for ffmpeg availability
- Shows installation instructions if missing
- Link to full dependency check

**Runtime Error Handling:**

- Catches and displays errors in UI
- Provides actionable error messages
- Suggests running dependency checker

## Typical Usage Scenarios

### Scenario 1: New Installation on Different Computer

```bash
# 1. Clone the repo
git clone <repo-url>
cd demo-video-analyzer

# 2. Check dependencies (before installing anything)
python3 check_dependencies.py
# Output: Shows what's missing

# 3. Follow instructions from output
brew install ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Verify installation
python check_dependencies.py
# Output: ✅ ALL CHECKS PASSED
```

### Scenario 2: Troubleshooting Failed Execution

```bash
# Try to run CLI
python cli/evaluate_video.py demo.mp4

# Get error: ModuleNotFoundError: No module named 'whisper'
# Error message suggests:
#   python check_dependencies.py

# Run dependency checker
python check_dependencies.py
# Output: Shows whisper is missing

# Install missing package
pip install openai-whisper

# Verify
python check_dependencies.py
# Output: ✅ ALL CHECKS PASSED
```

### Scenario 3: Streamlit App Won't Start

```bash
# Launch Streamlit
streamlit run app/reviewer.py

# App shows red error message:
#   "❌ Missing dependencies!"
#   With instructions to run check_dependencies.py

# Follow instructions
python check_dependencies.py
# See what's missing and fix
```

## Benefits

1. **Self-Documenting** - Checker shows exactly what's installed vs. needed
2. **Cross-Platform** - Works on macOS, Linux, Windows
3. **Helpful Errors** - Every error includes installation instructions
4. **Fast Diagnosis** - Single command to check everything
5. **CI/CD Ready** - Exit codes make it easy to use in automation
6. **User-Friendly** - Clear output with symbols (✓, ⚠️, ❌)

## Testing

All dependency checks verified:

```bash
# Run the checker
python check_dependencies.py
# Exit code: 0
# Output: ✅ ALL CHECKS PASSED

# Run CLI
python cli/evaluate_video.py --help
# Shows help with dependency check suggestion

# Test Streamlit (in browser)
streamlit run app/reviewer.py
# Sidebar shows: ✓ ffmpeg installed
```

## Future Enhancements

Possible additions:

- [ ] Check for GPU availability (CUDA/Metal)
- [ ] Verify API keys are set (without exposing values)
- [ ] Check disk space for Whisper model downloads
- [ ] Validate ffmpeg supports required codecs
- [ ] Auto-install missing pip packages (with confirmation)
- [ ] Generate detailed HTML report
- [ ] Integration with CI/CD (GitHub Actions, etc.)

## Summary

✅ **Dependency checker fully implemented and tested**
✅ **CLI and Streamlit app enhanced with helpful error messages**
✅ **README updated with dependency check instructions**
✅ **Works across different computers and environments**

**Result:** Users can now easily diagnose and fix dependency issues on any machine!
