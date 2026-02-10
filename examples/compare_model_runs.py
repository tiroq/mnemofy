"""Compare transcription runs with different models.

This script analyzes the run history file to compare performance
and quality across different model runs.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def load_run_history(history_path: Path) -> List[Dict[str, Any]]:
    """Load run history from JSONL file.
    
    Args:
        history_path: Path to .run-history.jsonl file
        
    Returns:
        List of run records sorted by timestamp
    """
    runs = []
    
    if not history_path.exists():
        print(f"No run history found at: {history_path}")
        return runs
    
    with open(history_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    run = json.loads(line)
                    runs.append(run)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid line: {e}")
    
    # Sort by timestamp
    runs.sort(key=lambda r: r.get("timestamp", ""))
    
    return runs


def display_run_comparison(runs: List[Dict[str, Any]]) -> None:
    """Display comparison table of all runs.
    
    Args:
        runs: List of run records
    """
    if not runs:
        print("No runs to compare.")
        return
    
    print("\n" + "=" * 100)
    print("MODEL RUN COMPARISON")
    print("=" * 100)
    
    # Header
    headers = ["#", "Date", "Model", "Duration", "Transcript", "Words", "Segments", "Config"]
    col_widths = [3, 19, 12, 10, 10, 8, 8, 30]
    
    header_line = ""
    for i, header in enumerate(headers):
        header_line += f"{header:<{col_widths[i]}} "
    print(f"\n{header_line}")
    print("-" * 100)
    
    # Rows
    for idx, run in enumerate(runs, 1):
        timestamp = run.get("timestamp", "N/A")
        if timestamp != "N/A":
            try:
                dt = datetime.fromisoformat(timestamp)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = timestamp[:16]
        else:
            date_str = "N/A"
        
        model = run.get("model", "N/A")
        duration = f"{run.get('duration_seconds', 0):.1f}s"
        transcript_dur = f"{run.get('transcript_duration', 0):.1f}s"
        words = str(run.get("word_count", 0))
        segments = str(run.get("segment_count", 0))
        
        config = run.get("config", {})
        config_str = f"lang={config.get('language', '?')}"
        if config.get("normalize"):
            config_str += ",norm"
        if config.get("repair"):
            config_str += ",repair"
        
        row = [
            str(idx),
            date_str,
            model,
            duration,
            transcript_dur,
            words,
            segments,
            config_str,
        ]
        
        row_line = ""
        for i, cell in enumerate(row):
            row_line += f"{cell:<{col_widths[i]}} "
        print(row_line)
    
    print("=" * 100)


def analyze_model_performance(runs: List[Dict[str, Any]]) -> None:
    """Analyze and compare model performance metrics.
    
    Args:
        runs: List of run records
    """
    if not runs:
        return
    
    print("\n" + "=" * 60)
    print("MODEL PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    # Group by model
    by_model = {}
    for run in runs:
        model = run.get("model", "unknown")
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(run)
    
    print(f"\nAnalyzed {len(runs)} run(s) across {len(by_model)} model(s)\n")
    
    for model, model_runs in sorted(by_model.items()):
        print(f"Model: {model}")
        print(f"  Runs: {len(model_runs)}")
        
        # Calculate averages
        avg_duration = sum(r.get("duration_seconds", 0) for r in model_runs) / len(model_runs)
        avg_words = sum(r.get("word_count", 0) for r in model_runs) / len(model_runs)
        avg_segments = sum(r.get("segment_count", 0) for r in model_runs) / len(model_runs)
        
        print(f"  Avg Processing Time: {avg_duration:.2f}s")
        print(f"  Avg Word Count: {avg_words:.0f}")
        print(f"  Avg Segments: {avg_segments:.0f}")
        
        # Latest config
        if model_runs:
            latest_config = model_runs[-1].get("config", {})
            print(f"  Latest Config:")
            print(f"    Language: {latest_config.get('language', 'N/A')}")
            print(f"    Meeting Type: {latest_config.get('meeting_type', 'N/A')}")
            print(f"    Normalized: {latest_config.get('normalize', False)}")
            print(f"    Repaired: {latest_config.get('repair', False)}")
        
        print()


def find_best_model(runs: List[Dict[str, Any]], metric: str = "speed") -> Dict[str, Any]:
    """Find the best model based on specified metric.
    
    Args:
        runs: List of run records
        metric: "speed" (fastest) or "quality" (most words/segments)
        
    Returns:
        Best run record
    """
    if not runs:
        return {}
    
    if metric == "speed":
        return min(runs, key=lambda r: r.get("duration_seconds", float("inf")))
    elif metric == "quality":
        # Use word count as quality proxy
        return max(runs, key=lambda r: r.get("word_count", 0))
    else:
        return runs[-1]  # Latest


def show_recommendations(runs: List[Dict[str, Any]]) -> None:
    """Show recommendations based on run history.
    
    Args:
        runs: List of run records
    """
    if len(runs) < 2:
        print("\nNeed at least 2 runs for recommendations.")
        return
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    fastest = find_best_model(runs, metric="speed")
    best_quality = find_best_model(runs, metric="quality")
    
    print(f"\n⚡ Fastest: {fastest.get('model', 'N/A')} "
          f"({fastest.get('duration_seconds', 0):.1f}s)")
    
    print(f"🎯 Best Quality: {best_quality.get('model', 'N/A')} "
          f"({best_quality.get('word_count', 0)} words)")
    
    # Check if there's a good balance
    speed_rank = sorted(runs, key=lambda r: r.get("duration_seconds", float("inf")))
    quality_rank = sorted(runs, key=lambda r: r.get("word_count", 0), reverse=True)
    
    for run in runs:
        speed_pos = speed_rank.index(run) + 1
        quality_pos = quality_rank.index(run) + 1
        balance_score = (speed_pos + quality_pos) / 2
        
        if balance_score <= len(runs) / 2:
            print(f"⚖️  Balanced: {run.get('model', 'N/A')} "
                  f"(speed rank: {speed_pos}/{len(runs)}, "
                  f"quality rank: {quality_pos}/{len(runs)})")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python compare_model_runs.py <path-to-run-history.jsonl>")
        print("\nExample:")
        print("  python compare_model_runs.py meeting.run-history.jsonl")
        sys.exit(1)
    
    history_file = Path(sys.argv[1])
    
    if not history_file.exists():
        print(f"Error: File not found: {history_file}")
        sys.exit(1)
    
    # Load and analyze runs
    runs = load_run_history(history_file)
    
    if not runs:
        print("No valid run records found.")
        sys.exit(0)
    
    # Display comparisons
    display_run_comparison(runs)
    analyze_model_performance(runs)
    show_recommendations(runs)
    
    print("\n" + "=" * 60)
    print(f"\nTotal runs analyzed: {len(runs)}")
    print(f"History file: {history_file}")
    print()
