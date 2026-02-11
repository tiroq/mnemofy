"""Compare transcription runs with different models.

This script analyzes the run history file to compare performance
and quality across different model runs.

NOTE: This functionality is now available as a CLI command:
    mnemofy compare-runs <history-file>
    mnemofy compare-runs --help

This example shows how to use the analysis module programmatically.
"""

from pathlib import Path

# Import analysis functions from mnemofy
from mnemofy.analysis import (
    load_run_history,
    display_run_comparison,
    analyze_model_performance,
    show_recommendations,
)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python compare_model_runs.py <path-to-run-history.jsonl>")
        print("\nExample:")
        print("  python compare_model_runs.py meeting.run-history.jsonl")
        print("\nOr use the CLI command:")
        print("  mnemofy compare-runs meeting.run-history.jsonl")
        sys.exit(1)
    
    history_file = Path(sys.argv[1])
    
    if not history_file.exists():
        print(f"Error: File not found: {history_file}")
        sys.exit(1)
    
    # Load and analyze runs (use_rich=False for plain text output)
    runs = load_run_history(history_file)
    
    if not runs:
        print("No valid run records found.")
        sys.exit(0)
    
    # Display comparisons
    display_run_comparison(runs, use_rich=False)
    analyze_model_performance(runs, use_rich=False)
    show_recommendations(runs, use_rich=False)
    
    print("\n" + "=" * 60)
    print(f"\nTotal runs analyzed: {len(runs)}")
    print(f"History file: {history_file}")
    print("\nTIP: Use the CLI for a better experience with rich formatting:")
    print(f"  mnemofy compare-runs {history_file}")
    print()
