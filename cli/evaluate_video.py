#!/usr/bin/env python3
import sys
import os
# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import subprocess
from io import StringIO

def paginate_output(content: str):
    """Display output with pagination using less or more."""
    # Check if output is being piped or redirected
    if not sys.stdout.isatty():
        # Output is piped/redirected, just print normally
        print(content)
        return
    
    # Try to use less with nice options, fall back to more, or just print
    pagers = [
        ['less', '-R', '-F', '-X'],  # -R: color codes, -F: quit if one screen, -X: no clear screen
        ['more'],
    ]
    
    for pager_cmd in pagers:
        try:
            # Try to find the pager
            subprocess.run(['which', pager_cmd[0]], capture_output=True, check=True)
            
            # Pager exists, use it
            process = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE, text=True)
            try:
                process.communicate(input=content)
                return
            except (BrokenPipeError, KeyboardInterrupt):
                # User quit the pager
                return
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Pager not found, try next one
            continue
    
    # No pager available, just print
    print(content)

def main():
    # Check critical imports and provide helpful error messages
    try:
        from src.video_evaluator import VideoEvaluator, AIProvider, list_available_rubrics, save_results
    except ImportError as e:
        print("=" * 70)
        print("ERROR: Missing dependencies")
        print("=" * 70)
        print(f"\n{e}\n")
        print("Some required Python packages are not installed.")
        print("\nTo check which dependencies are missing, run:")
        print("  python check_dependencies.py")
        print("\nTo install all dependencies:")
        print("  pip install -r requirements.txt")
        print()
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='Evaluate demo videos using AI',
        epilog='Run "python check_dependencies.py" to verify all dependencies are installed.\n\nExample: python cli/evaluate_video.py test_data/realistic_demo.wav --first-name "John" --last-name "Doe" --partner-name "Jane Smith"'
    )
    parser.add_argument('file', nargs='?', help='Path to local video or audio file')
    parser.add_argument('--provider', choices=['openai','anthropic'], default='openai')
    parser.add_argument('--vision', action='store_true', help='Enable visual alignment checks')
    parser.add_argument('--rubric', type=str, default='default', 
                        help='Rubric to use for evaluation (default: default). Use --list-rubrics to see available options.')
    parser.add_argument('--list-rubrics', action='store_true', 
                        help='List all available rubrics and exit')
    parser.add_argument('--no-translate', action='store_true', 
                        help='Disable automatic translation to English (translation is enabled by default)')
    parser.add_argument('--first-name', type=str,
                        help='First name of the submitter (required for evaluation)')
    parser.add_argument('--last-name', type=str,
                        help='Last name of the submitter (required for evaluation)')
    parser.add_argument('--partner-name', type=str,
                        help='Partner name for the submission (required for evaluation)')
    args = parser.parse_args()
    
    # Handle --list-rubrics command
    if args.list_rubrics:
        print("\n" + "=" * 70)
        print("AVAILABLE RUBRICS")
        print("=" * 70 + "\n")
        rubrics = list_available_rubrics()
        for rubric in rubrics:
            print(f"📋 {rubric['name']}")
            print(f"   Filename: {rubric['filename']}")
            print(f"   Description: {rubric['description']}")
            print()
        print("Usage: --rubric <filename>")
        print("Example: python cli/evaluate_video.py video.mp4 --rubric sales-demo --first-name \"John\" --last-name \"Doe\" --partner-name \"Jane Smith\"")
        print()
        sys.exit(0)
    
    # Validate required submitter arguments for evaluation
    if not args.first_name or not args.last_name or not args.partner_name:
        parser.error("the following arguments are required for evaluation: --first-name, --last-name, --partner-name")
    
    # Require file if not listing rubrics
    if not args.file:
        parser.error("the following arguments are required: file (use --list-rubrics to list available rubrics)")
    
    # Verify that the file exists
    if not os.path.exists(args.file):
        print("=" * 70)
        print("ERROR: File not found")
        print("=" * 70)
        print(f"\nThe file '{args.file}' does not exist.")
        print("\nUsage: python cli/evaluate_video.py <file_path> --first-name <name> --last-name <name> --partner-name <name>")
        print("Example: python cli/evaluate_video.py test_data/realistic_demo.wav --first-name \"John\" --last-name \"Doe\" --partner-name \"Jane Smith\"")
        print()
        sys.exit(1)

    try:
        print("\n🎬 Starting video analysis...")
        print(f"📋 Using rubric: {args.rubric}")
        # Translation is enabled by default unless --no-translate is specified
        translate_enabled = not args.no_translate
        if args.no_translate:
            print("🌐 Translation disabled: Will keep original language")
        
        provider = AIProvider.OPENAI if args.provider == 'openai' else AIProvider.ANTHROPIC
        # Progress callback for CLI
        def cli_progress_callback(message: str):
            print(message, flush=True)
        
        evaluator = VideoEvaluator(
            provider=provider, 
            enable_vision=args.vision, 
            rubric_name=args.rubric,
            translate_to_english=translate_enabled,
            progress_callback=cli_progress_callback
        )
        result = evaluator.process(args.file, is_url=False, enable_vision=args.vision)
        
        # Add submitter information to results
        result['submitter'] = {
            'first_name': args.first_name.strip(),
            'last_name': args.last_name.strip(),
            'partner_name': args.partner_name.strip()
        }
        
        print("✓ Analysis complete!\n")
        
        # Capture all output in a buffer for pagination
        output = StringIO()
        
        # Print formatted output to buffer
        output.write("\n" + "=" * 70 + "\n")
        output.write("DEMO VIDEO EVALUATION RESULTS\n")
        output.write("=" * 70 + "\n\n")
        
        # Evaluation summary (moved to top)
        evaluation = result.get('evaluation', {})
        overall = evaluation.get('overall', {})
        
        # Check if using new rubric format (has categories)
        is_new_format = 'categories' in evaluation
        
        # Status first with emoji
        status = overall.get('pass_status', 'unknown').upper()
        status_emoji = "🟢" if status == "PASS" else ("🟡" if status == "REVISE" else "🔴")
        output.write(f"Status: {status_emoji} {status}\n")
        
        # Overall Score second
        if is_new_format:
            total_points = overall.get('total_points', 0)
            max_points = overall.get('max_points', 50)
            percentage = overall.get('percentage', 0)
            output.write(f"Overall Score: {total_points}/{max_points} ({percentage:.1f}%)\n")
        else:
            output.write(f"Overall Score: {overall.get('weighted_score', 0):.1f}/10\n")
        
        # Display category breakdown for new format
        if is_new_format and 'categories' in evaluation:
            output.write("Category Breakdown:\n")
            categories = evaluation.get('categories', {})
            for cat_id, cat_data in categories.items():
                cat_name = cat_id.replace('_', ' ').title()
                points = cat_data.get('points', 0)
                max_points = cat_data.get('max_points', 0)
                percentage = cat_data.get('percentage', 0)
                output.write(f"  {cat_name}: {points}/{max_points} ({percentage:.1f}%)\n")
            output.write("\n")
        
        # Display short summary
        short_summary = evaluation.get('short_summary', '')
        if short_summary:
            output.write(f"Summary: {short_summary}\n")
        output.write("\n")
        
        # Transcription quality (moved below evaluation summary, no emoji)
        quality = result.get('quality', {})
        if quality:
            quality_rating = quality.get('quality_rating', 'unknown').upper()
            
            output.write(f"Transcription Quality: {quality_rating}\n")
            
            # Display detected language (with translation indicator if applicable)
            language = result.get('language', 'unknown')
            if translate_enabled and language.lower() != 'en':
                output.write(f"  Detected Language: {language.upper()} → 🌐 Translated to English\n")
                output.write(f"    (Audio was translated to English by Whisper)\n")
            else:
                output.write(f"  Detected Language: {language.upper()}\n")
                output.write(f"    (Language automatically detected by Whisper)\n")
            
            output.write(f"  Confidence: {quality.get('avg_confidence', 0):.1f}%\n")
            output.write(f"    (How certain Whisper is about the transcription)\n")
            output.write(f"  Speech Detection: {quality.get('speech_percentage', 0):.1f}%\n")
            output.write(f"    (Percentage of audio detected as speech vs. silence/noise)\n")
            output.write(f"  Compression Ratio: {quality.get('avg_compression_ratio', 0):.2f}\n")
            output.write(f"    (Text length vs. audio duration; 1.5-2.5 is typical)\n")
            
            warnings = quality.get('warnings', [])
            if warnings:
                output.write(f"\n  ⚠️  Quality Warnings:\n")
                for warning in warnings:
                    output.write(f"     - {warning}\n")
            output.write("\n")
        
        # Feedback section
        feedback = result.get('feedback', {})
        if feedback:
            tone = feedback.get('tone', 'supportive')
            output.write("-" * 70 + "\n")
            output.write(f"FEEDBACK ({tone.upper()} TONE)\n")
            output.write("-" * 70 + "\n\n")
            
            output.write("✓ STRENGTHS:\n\n")
            for i, strength in enumerate(feedback.get('strengths', []), 1):
                output.write(f"{i}. {strength.get('title', 'Strength')}\n")
                output.write(f"   {strength.get('description', '')}\n\n")
            
            output.write("→ AREAS FOR IMPROVEMENT:\n\n")
            for i, improvement in enumerate(feedback.get('improvements', []), 1):
                output.write(f"{i}. {improvement.get('title', 'Area for improvement')}\n")
                output.write(f"   {improvement.get('description', '')}\n\n")
        
        output.write("-" * 70 + "\n")
        output.write("\nFull JSON output:\n")
        output.write("-" * 70 + "\n")
        import json
        output.write(json.dumps(result, indent=2) + "\n")
        
        # Save results to file
        saved_path = save_results(result, args.file, output_format='json')
        
        # Send all output through pager
        paginate_output(output.getvalue())
        
        # Notify user about saved results (after pagination)
        print(f"\n💾 Results saved to: {saved_path}")
        
    except FileNotFoundError as e:
        if 'ffmpeg' in str(e).lower():
            print("=" * 70)
            print("ERROR: ffmpeg not found")
            print("=" * 70)
            print("\nffmpeg is required for video/audio processing.")
            print("\nTo install ffmpeg:")
            print("  macOS: brew install ffmpeg")
            print("  Linux: sudo apt-get install ffmpeg")
            print("\nTo check all dependencies, run:")
            print("  python check_dependencies.py")
            print()
            sys.exit(1)
        else:
            raise
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nIf you're seeing dependency errors, run:")
        print("  python check_dependencies.py")
        print()
        sys.exit(1)

if __name__ == '__main__':
    main()
