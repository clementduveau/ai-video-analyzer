# Quick Reference: Results Saving

## What Was Implemented

✅ **Automatic results saving** to `results/` folder after each evaluation  
✅ **Timestamped filenames** to prevent overwrites and preserve history  
✅ **Two formats**: Human-readable text (.txt) and machine-readable JSON (.json)  
✅ **CLI integration**: Shows save confirmation after pagination  
✅ **UI integration**: Download buttons for both formats  
✅ **Privacy**: Results folder is git-ignored

## File Locations

### CLI

- **Saved format**: Text only
- **Location**: `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
- **Example**: `results/realistic_demo_results_20251010_130222.txt`

### UI (Streamlit)

- **Saved formats**: Text AND JSON
- **Locations**:
  - `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
  - `results/<filename>_results_YYYYMMDD_HHMMSS.json`
- **Plus**: Download buttons in the UI

## Quick Usage

### CLI

```bash
# Run evaluation
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai

# Results auto-saved with timestamp, confirmation shown:
# 💾 Results saved to: results/realistic_demo_results_20251010_130222.txt

# Run again - creates NEW file (no overwrite)
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai
# 💾 Results saved to: results/realistic_demo_results_20251010_143015.txt

# View all results for this file
ls results/realistic_demo_results_*.txt
```

### UI

```bash
# Start UI
streamlit run app/reviewer.py

# 1. Upload video/audio
# 2. Click "Evaluate Video"
# 3. See results
# 4. See: "💾 Results saved to results/ folder"
# 5. Click download buttons for text or JSON
```

## File Structure

### Text Format (.txt)

- Complete evaluation results
- Feedback section (strengths + improvements)
- Full transcript
- Quality metrics
- JSON output at the end

### JSON Format (.json)

- Same data as text, but in JSON structure
- Perfect for programmatic access
- Includes all evaluation details

## Key Files Modified

1. **src/video_evaluator.py**

   - Added `save_results()` function
   - Handles both text and JSON formats

2. **cli/evaluate_video.py**

   - Imports `save_results`
   - Calls it after evaluation
   - Shows confirmation message

3. **app/reviewer.py**

   - Imports `save_results`
   - Saves both formats
   - Adds download buttons

4. **results/** (new directory)

   - `.gitignore` - ignores result files
   - `README.md` - comprehensive documentation

5. **README.md**
   - Added "Results Storage" section
   - Updated project structure

## Documentation Created

1. **results/README.md** - Complete results documentation
2. **RESULTS_FEATURE.md** - Implementation details and use cases
3. **README.md** - User-facing documentation updated

## Testing Performed

✅ CLI saves text results correctly (357 lines)  
✅ JSON format saves and loads correctly  
✅ File naming convention works  
✅ Git ignore configuration in place  
✅ Confirmation messages display properly

## What Users See

### CLI Output (end of evaluation)

```
... paginated output ...

💾 Results saved to: /path/to/results/realistic_demo_results.txt
```

### UI Output (after evaluation)

```
✅ Success message: "💾 Results saved to results/ folder"
📄 [Download Text Report] button
📊 [Download JSON Data] button
```

## Privacy & Git

The `results/.gitignore` file ensures:

- All `.txt` files are ignored
- All `.json` files are ignored
- Only `.gitignore` and `README.md` are tracked
- Results stay local and private

## Benefits

- **Never lose results** - Auto-saved every time
- **Easy sharing** - Send text file to submitters
- **Automation ready** - JSON format for scripts
- **Archive friendly** - Move old results to dated folders
- **Privacy first** - Not committed to git

---

**Status**: ✅ Complete and tested  
**Ready for**: Production use
