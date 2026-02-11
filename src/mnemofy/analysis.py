"""Analysis utilities for metadata and run history."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rich.console import Console
from rich.table import Table


console = Console()


# ============================================================================
# Metadata Analysis
# ============================================================================


def analyze_processing_metadata(metadata_path: Path, use_rich: bool = True) -> None:
    """Analyze processing metadata and print summary.
    
    Args:
        metadata_path: Path to metadata JSON file
        use_rich: Use rich console formatting (default: True)
    """
    with open(metadata_path, encoding="utf-8") as f:
        metadata = json.load(f)
    
    if use_rich:
        console.print("\n[bold cyan]PROCESSING METADATA ANALYSIS[/bold cyan]")
        console.print("=" * 60)
        
        # Basic info
        console.print(f"\n[bold]Input File:[/bold] {metadata['input_file']}")
        console.print(f"[bold]Processing Time:[/bold] {metadata['duration_seconds']:.2f}s")
        
        # ASR model info
        asr = metadata['asr_engine']
        console.print(f"\n[bold]ASR Model:[/bold] {asr['engine']} / {asr['model']}")
        if asr.get('model_size_gb'):
            console.print(f"  • Model Size: {asr['model_size_gb']} GB")
            console.print(f"  • Quality Rating: {asr.get('quality_rating', 'N/A')}/5")
            console.print(f"  • Speed Rating: {asr.get('speed_rating', 'N/A')}/5")
        
        # LLM model info (if used)
        if metadata.get('llm_engine'):
            llm = metadata['llm_engine']
            console.print(f"\n[bold]LLM Model:[/bold] {llm['engine']} / {llm['model']}")
            console.print(f"  • Purpose: {llm['purpose']}")
        
        # Processing config
        config = metadata['config']
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  • Language: {config['language']}")
        console.print(f"  • Normalized: {config['normalize']}")
        console.print(f"  • Repaired: {config['repair']}")
        if config.get('meeting_type'):
            console.print(f"  • Meeting Type: {config['meeting_type']}")
        
        # Statistics
        console.print(f"\n[bold]Transcript Statistics:[/bold]")
        console.print(f"  • Duration: {metadata.get('transcript_duration_seconds', 0):.1f}s")
        console.print(f"  • Segments: {metadata.get('segment_count', 0)}")
        console.print(f"  • Words: {metadata.get('word_count', 0)}")
    else:
        # Plain text output (for non-rich environments)
        print("=" * 60)
        print("PROCESSING METADATA ANALYSIS")
        print("=" * 60)
        
        print(f"\nInput File: {metadata['input_file']}")
        print(f"Processing Time: {metadata['duration_seconds']:.2f}s")
        
        asr = metadata['asr_engine']
        print(f"\nASR Model: {asr['engine']} / {asr['model']}")
        if asr.get('model_size_gb'):
            print(f"  - Model Size: {asr['model_size_gb']} GB")
            print(f"  - Quality Rating: {asr.get('quality_rating', 'N/A')}/5")
            print(f"  - Speed Rating: {asr.get('speed_rating', 'N/A')}/5")
        
        if metadata.get('llm_engine'):
            llm = metadata['llm_engine']
            print(f"\nLLM Model: {llm['engine']} / {llm['model']}")
            print(f"  - Purpose: {llm['purpose']}")
        
        config = metadata['config']
        print(f"\nConfiguration:")
        print(f"  - Language: {config['language']}")
        print(f"  - Normalized: {config['normalize']}")
        print(f"  - Repaired: {config['repair']}")
        if config.get('meeting_type'):
            print(f"  - Meeting Type: {config['meeting_type']}")
        
        print(f"\nTranscript Statistics:")
        print(f"  - Duration: {metadata.get('transcript_duration_seconds', 0):.1f}s")
        print(f"  - Segments: {metadata.get('segment_count', 0)}")
        print(f"  - Words: {metadata.get('word_count', 0)}")


def analyze_artifacts_manifest(manifest_path: Path, use_rich: bool = True) -> None:
    """Analyze artifacts manifest and print summary.
    
    Args:
        manifest_path: Path to artifacts manifest JSON file
        use_rich: Use rich console formatting (default: True)
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    
    if use_rich:
        console.print("\n[bold cyan]ARTIFACTS MANIFEST ANALYSIS[/bold cyan]")
        console.print("=" * 60)
        
        console.print(f"\n[bold]Input File:[/bold] {manifest['input_file']}")
        console.print(f"[bold]Primary Model:[/bold] {manifest.get('model_name', 'N/A')}")
        console.print(f"[bold]Generated At:[/bold] {manifest['generated_at']}")
        console.print(f"[bold]Total Size:[/bold] {manifest['total_size_bytes'] / 1024:.2f} KB")
        
        console.print(f"\n[bold]Artifacts by Type:[/bold]")
        for artifact_type, artifacts in manifest['artifacts_by_type'].items():
            console.print(f"\n  [yellow]{artifact_type.upper()}:[/yellow]")
            for artifact in artifacts:
                size_kb = artifact.get('size_bytes', 0) / 1024
                model = artifact.get('model_used', 'N/A')
                console.print(f"    • {artifact['path']}")
                console.print(f"      Format: {artifact['format']}, Size: {size_kb:.2f} KB")
                console.print(f"      Model: {model}")
    else:
        print("\n" + "=" * 60)
        print("ARTIFACTS MANIFEST ANALYSIS")
        print("=" * 60)
        
        print(f"\nInput File: {manifest['input_file']}")
        print(f"Primary Model: {manifest.get('model_name', 'N/A')}")
        print(f"Generated At: {manifest['generated_at']}")
        print(f"Total Size: {manifest['total_size_bytes'] / 1024:.2f} KB")
        
        print(f"\nArtifacts by Type:")
        for artifact_type, artifacts in manifest['artifacts_by_type'].items():
            print(f"\n  {artifact_type.upper()}:")
            for artifact in artifacts:
                size_kb = artifact.get('size_bytes', 0) / 1024
                model = artifact.get('model_used', 'N/A')
                print(f"    • {artifact['path']}")
                print(f"      Format: {artifact['format']}, Size: {size_kb:.2f} KB")
                print(f"      Model: {model}")


def compare_transcript_metadata(json_paths: List[Path], use_rich: bool = True) -> None:
    """Compare metadata from multiple transcript JSON files.
    
    Args:
        json_paths: List of paths to transcript JSON files
        use_rich: Use rich console formatting (default: True)
    """
    metadatas: List[Tuple[str, Dict[str, Any]]] = []
    for path in json_paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            metadatas.append((path.name, data.get('metadata', {})))
    
    if use_rich:
        console.print("\n[bold cyan]TRANSCRIPT COMPARISON[/bold cyan]")
        console.print(f"Comparing {len(metadatas)} transcripts\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("File", style="cyan", width=30)
        table.add_column("Model", width=12)
        table.add_column("Quality", justify="center", width=8)
        table.add_column("Speed", justify="center", width=6)
        table.add_column("Words", justify="right", width=8)
        table.add_column("Segments", justify="right", width=8)
        
        for filename, metadata in metadatas:
            model = str(metadata.get('model', 'N/A'))
            quality = str(metadata.get('quality_rating', 'N/A'))
            speed = str(metadata.get('speed_rating', 'N/A'))
            words = str(metadata.get('word_count', 0))
            segments = str(metadata.get('segment_count', 0))
            
            table.add_row(filename, model, quality, speed, words, segments)
        
        console.print(table)
    else:
        print("\n" + "=" * 60)
        print("TRANSCRIPT COMPARISON")
        print("=" * 60)
        
        print(f"\nComparing {len(metadatas)} transcripts:\n")
        
        headers = ["File", "Model", "Quality", "Speed", "Words", "Segments"]
        print(f"{headers[0]:30} {headers[1]:10} {headers[2]:8} {headers[3]:6} {headers[4]:8} {headers[5]:8}")
        print("-" * 80)
        
        for filename, metadata in metadatas:
            model = metadata.get('model', 'N/A')
            quality = metadata.get('quality_rating', 'N/A')
            speed = metadata.get('speed_rating', 'N/A')
            words = metadata.get('word_count', 0)
            segments = metadata.get('segment_count', 0)
            
            print(f"{filename:30} {str(model):10} {str(quality):8} {str(speed):6} {words:8} {segments:8}")


def calculate_processing_cost(metadata_path: Path, use_rich: bool = True) -> None:
    """Estimate LLM processing cost based on usage.
    
    Args:
        metadata_path: Path to metadata JSON file
        use_rich: Use rich console formatting (default: True)
    """
    with open(metadata_path, encoding="utf-8") as f:
        metadata = json.load(f)
    
    if not metadata.get('llm_engine'):
        if use_rich:
            console.print("\n[yellow]No LLM usage detected.[/yellow]")
        else:
            print("\nNo LLM usage detected.")
        return
    
    if use_rich:
        console.print("\n[bold cyan]LLM COST ESTIMATION[/bold cyan]")
        console.print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("LLM COST ESTIMATION")
        print("=" * 60)
    
    llm = metadata['llm_engine']
    word_count = metadata.get('word_count', 0)
    
    # Rough token estimation (words * 1.3 for English)
    estimated_tokens = int(word_count * 1.3)
    
    if use_rich:
        console.print(f"\n[bold]LLM Model:[/bold] {llm['model']}")
        console.print(f"[bold]Purpose:[/bold] {llm['purpose']}")
        console.print(f"[bold]Estimated Input Tokens:[/bold] ~{estimated_tokens:,}")
    else:
        print(f"\nLLM Model: {llm['model']}")
        print(f"Purpose: {llm['purpose']}")
        print(f"Estimated Input Tokens: ~{estimated_tokens:,}")
    
    # Cost estimation (example rates - adjust based on actual pricing)
    if 'gpt-4o' in llm['model']:
        cost_per_1k = 0.005  # Example rate
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k
        if use_rich:
            console.print(f"[bold]Estimated Cost:[/bold] [green]${estimated_cost:.4f} USD[/green]")
        else:
            print(f"Estimated Cost: ${estimated_cost:.4f} USD")
    elif 'ollama' in llm['engine']:
        if use_rich:
            console.print("[bold]Cost:[/bold] [green]$0.00 (local model)[/green]")
        else:
            print("Cost: $0.00 (local model)")
    else:
        if use_rich:
            console.print("[yellow]Cost estimation not available for this model[/yellow]")
        else:
            print("Cost estimation not available for this model")


# ============================================================================
# Run History Analysis
# ============================================================================


def load_run_history(history_path: Path) -> List[Dict[str, Any]]:
    """Load run history from JSONL file.
    
    Args:
        history_path: Path to .run-history.jsonl file
        
    Returns:
        List of run records sorted by timestamp
    """
    runs = []
    
    if not history_path.exists():
        console.print(f"[yellow]No run history found at: {history_path}[/yellow]")
        return runs
    
    with open(history_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    run = json.loads(line)
                    runs.append(run)
                except json.JSONDecodeError as e:
                    console.print(f"[yellow]Warning: Skipping invalid line: {e}[/yellow]")
    
    # Sort by timestamp
    runs.sort(key=lambda r: r.get("timestamp", ""))
    
    return runs


def display_run_comparison(runs: List[Dict[str, Any]], use_rich: bool = True) -> None:
    """Display comparison table of all runs.
    
    Args:
        runs: List of run records
        use_rich: Use rich console formatting (default: True)
    """
    if not runs:
        if use_rich:
            console.print("[yellow]No runs to compare.[/yellow]")
        else:
            print("No runs to compare.")
        return
    
    if use_rich:
        console.print("\n[bold cyan]MODEL RUN COMPARISON[/bold cyan]")
        console.print("=" * 100)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", justify="right", width=3)
        table.add_column("Date", width=19)
        table.add_column("Model", width=12)
        table.add_column("Duration", justify="right", width=10)
        table.add_column("Transcript", justify="right", width=10)
        table.add_column("Words", justify="right", width=8)
        table.add_column("Segments", justify="right", width=8)
        table.add_column("Config", width=30)
        
        for idx, run in enumerate(runs, 1):
            timestamp = run.get("timestamp", "N/A")
            if timestamp != "N/A":
                try:
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
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
            
            table.add_row(str(idx), date_str, model, duration, transcript_dur, words, segments, config_str)
        
        console.print(table)
        console.print("=" * 100)
    else:
        print("\n" + "=" * 100)
        print("MODEL RUN COMPARISON")
        print("=" * 100)
        
        headers = ["#", "Date", "Model", "Duration", "Transcript", "Words", "Segments", "Config"]
        col_widths = [3, 19, 12, 10, 10, 8, 8, 30]
        
        header_line = ""
        for i, header in enumerate(headers):
            header_line += f"{header:<{col_widths[i]}} "
        print(f"\n{header_line}")
        print("-" * 100)
        
        for idx, run in enumerate(runs, 1):
            timestamp = run.get("timestamp", "N/A")
            if timestamp != "N/A":
                try:
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
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


def analyze_model_performance(runs: List[Dict[str, Any]], use_rich: bool = True) -> None:
    """Analyze and compare model performance metrics.
    
    Args:
        runs: List of run records
        use_rich: Use rich console formatting (default: True)
    """
    if not runs:
        return
    
    if use_rich:
        console.print("\n[bold cyan]MODEL PERFORMANCE ANALYSIS[/bold cyan]")
        console.print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("MODEL PERFORMANCE ANALYSIS")
        print("=" * 60)
    
    # Group by model
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    for run in runs:
        model = run.get("model", "unknown")
        if model not in by_model:
            by_model[model] = []
        by_model[model].append(run)
    
    if use_rich:
        console.print(f"\nAnalyzed {len(runs)} run(s) across {len(by_model)} model(s)\n")
    else:
        print(f"\nAnalyzed {len(runs)} run(s) across {len(by_model)} model(s)\n")
    
    for model, model_runs in sorted(by_model.items()):
        if use_rich:
            console.print(f"[bold]Model:[/bold] [cyan]{model}[/cyan]")
            console.print(f"  Runs: {len(model_runs)}")
        else:
            print(f"Model: {model}")
            print(f"  Runs: {len(model_runs)}")
        
        # Calculate averages
        avg_duration = sum(r.get("duration_seconds", 0) for r in model_runs) / len(model_runs)
        avg_words = sum(r.get("word_count", 0) for r in model_runs) / len(model_runs)
        avg_segments = sum(r.get("segment_count", 0) for r in model_runs) / len(model_runs)
        
        if use_rich:
            console.print(f"  Avg Processing Time: {avg_duration:.2f}s")
            console.print(f"  Avg Word Count: {avg_words:.0f}")
            console.print(f"  Avg Segments: {avg_segments:.0f}")
        else:
            print(f"  Avg Processing Time: {avg_duration:.2f}s")
            print(f"  Avg Word Count: {avg_words:.0f}")
            print(f"  Avg Segments: {avg_segments:.0f}")
        
        # Latest config
        if model_runs:
            latest_config = model_runs[-1].get("config", {})
            if use_rich:
                console.print(f"  Latest Config:")
                console.print(f"    Language: {latest_config.get('language', 'N/A')}")
                console.print(f"    Meeting Type: {latest_config.get('meeting_type', 'N/A')}")
                console.print(f"    Normalized: {latest_config.get('normalize', False)}")
                console.print(f"    Repaired: {latest_config.get('repair', False)}")
            else:
                print(f"  Latest Config:")
                print(f"    Language: {latest_config.get('language', 'N/A')}")
                print(f"    Meeting Type: {latest_config.get('meeting_type', 'N/A')}")
                print(f"    Normalized: {latest_config.get('normalize', False)}")
                print(f"    Repaired: {latest_config.get('repair', False)}")
        
        if use_rich:
            console.print()
        else:
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


def show_recommendations(runs: List[Dict[str, Any]], use_rich: bool = True) -> None:
    """Show recommendations based on run history.
    
    Args:
        runs: List of run records
        use_rich: Use rich console formatting (default: True)
    """
    if len(runs) < 2:
        if use_rich:
            console.print("\n[yellow]Need at least 2 runs for recommendations.[/yellow]")
        else:
            print("\nNeed at least 2 runs for recommendations.")
        return
    
    if use_rich:
        console.print("\n[bold cyan]RECOMMENDATIONS[/bold cyan]")
        console.print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
    
    fastest = find_best_model(runs, metric="speed")
    best_quality = find_best_model(runs, metric="quality")
    
    if use_rich:
        console.print(f"\n⚡ [bold]Fastest:[/bold] [green]{fastest.get('model', 'N/A')}[/green] "
                     f"({fastest.get('duration_seconds', 0):.1f}s)")
        console.print(f"🎯 [bold]Best Quality:[/bold] [green]{best_quality.get('model', 'N/A')}[/green] "
                     f"({best_quality.get('word_count', 0)} words)")
    else:
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
            if use_rich:
                console.print(f"⚖️  [bold]Balanced:[/bold] [green]{run.get('model', 'N/A')}[/green] "
                             f"(speed rank: {speed_pos}/{len(runs)}, "
                             f"quality rank: {quality_pos}/{len(runs)})")
            else:
                print(f"⚖️  Balanced: {run.get('model', 'N/A')} "
                      f"(speed rank: {speed_pos}/{len(runs)}, "
                      f"quality rank: {quality_pos}/{len(runs)})")
            break
