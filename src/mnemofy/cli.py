"""Command-line interface for mnemofy."""

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import click
import readchar
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.audio import AudioExtractor
from mnemofy.model_selector import (
    ModelSelectionError,
    filter_compatible_models,
    get_model_table,
    list_models,
    recommend_model,
)
from mnemofy.notes import StructuredNotesGenerator
from mnemofy.output_manager import OutputManager
from mnemofy.pipeline import PipelineConfig, PipelineContext, TranscribePipeline
from mnemofy.resources import detect_system_resources
from mnemofy.transcriber import Transcriber
from mnemofy.tui.model_menu import ModelMenu, is_interactive_environment

app = typer.Typer(
    name="mnemofy",
    help="Extract audio from media files, transcribe speech, and produce documented meeting notes",
    add_completion=False,
)
console = Console()
logger = logging.getLogger(__name__)


@app.command()
def transcribe(
    input_file: Optional[Path] = typer.Argument(
        None,
        help="Path to audio or video file (aac, mp3, wav, mkv, mp4). Not required when using --list-models.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output Markdown file path (default: input_name_notes.md)",
    ),
    outdir: Optional[Path] = typer.Option(
        None,
        "--outdir",
        help="Output directory for transcript and notes files (default: same as input)",
        file_okay=False,
        dir_okay=True,
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Whisper model to use (tiny, base, small, medium, large-v3). "
        "If not provided, auto-detects based on system resources. "
        "Use --list-models to see all available models.",
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Auto-select model without interactive menu (headless mode). "
        "Uses system resource detection to recommend best model.",
    ),
    no_gpu: bool = typer.Option(
        False,
        "--no-gpu",
        help="Force CPU-only mode, disable GPU acceleration if available",
    ),
    list_models_flag: bool = typer.Option(
        False,
        "--list-models",
        help="Display available models and exit (does not transcribe)",
    ),
    title: str = typer.Option(
        "Meeting Notes",
        "--title",
        "-t",
        help="Title for the generated notes",
    ),
    keep_audio: bool = typer.Option(
        False,
        "--keep-audio",
        "-k",
        help="Keep extracted audio file",
    ),
    lang: Optional[str] = typer.Option(
        None,
        "--lang",
        help="Language of audio (e.g., en, es, fr). Auto-detect if not specified",
    ),
    notes: str = typer.Option(
        "basic",
        "--notes",
        help="Notes generation mode: 'basic' (deterministic) or 'llm' (LLM-enhanced)",
    ),
    meeting_type: Optional[str] = typer.Option(
        "auto",
        "--meeting-type",
        help="Meeting type: auto (detect), status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm",
    ),
    classify: str = typer.Option(
        "heuristic",
        "--classify",
        help="Classification mode: heuristic (default), llm, or off (disable detection)",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        help="Custom template file path (overrides default meeting type templates)",
    ),
    llm_engine: str = typer.Option(
        "openai",
        "--llm-engine",
        help="LLM engine: openai (default), ollama, or openai_compat",
    ),
    llm_model: Optional[str] = typer.Option(
        None,
        "--llm-model",
        help="LLM model name (default: gpt-4o-mini for openai, llama3.2:3b for ollama)",
    ),
    llm_base_url: Optional[str] = typer.Option(
        None,
        "--llm-base-url",
        help="Custom LLM API base URL (for openai_compat or custom endpoints)",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Skip interactive prompts (auto-accept detected meeting type)",
    ),
    normalize: bool = typer.Option(
        False,
        "--normalize",
        help="Apply deterministic transcript normalization (stutter reduction, sentence stitching)",
    ),
    repair: bool = typer.Option(
        False,
        "--repair",
        help="Use LLM to repair ASR errors (requires LLM engine, outputs change log)",
    ),
    remove_fillers: bool = typer.Option(
        False,
        "--remove-fillers",
        help="Remove filler words (um, uh, like) during normalization (use with --normalize)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging (shows LLM request details, timing, detection info)",
    ),
    model_suffix: bool = typer.Option(
        False,
        "--model-suffix",
        help="Include model name in output filenames (e.g., meeting.base.transcript.json). "
        "Useful for comparing outputs from different models without overwriting.",
    ),
) -> None:
    """
    Transcribe audio/video file and generate structured meeting notes.

    The tool will:
    1. Detect system resources and recommend appropriate Whisper model
    2. Extract audio from the media file (if needed)
    3. Transcribe speech using recommended or specified model
    4. Generate structured Markdown notes with topics, decisions, actions, and mentions

    Model Selection Behavior:
    - With --model: Uses specified model (explicit override)
    - With --auto: Auto-selects without interactive menu
    - With TTY (interactive terminal): Shows interactive model menu
    - Non-TTY (piped input, CI/CD): Auto-selects silently
    - Fallback: Uses 'base' model if detection fails
    """
    # Configure logging based on verbose flag
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='[%(levelname)s] %(message)s',
        force=True
    )
    
    # Detect if --repair was explicitly requested (vs defaulted)
    try:
        ctx = click.get_current_context(silent=True)
        repair_source = ctx.get_parameter_source("repair") if ctx else None
        repair_requested = (
            repair_source is not None
            and repair_source != click.core.ParameterSource.DEFAULT
        )
    except Exception:
        repair_requested = repair
    
    # Handle --list-models flag (exit early, without pipeline)
    if list_models_flag:
        try:
            resources = detect_system_resources(no_gpu=no_gpu)
            table = get_model_table(resources, use_gpu=not no_gpu)
            console.print(table)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not detect system resources: {e}")
            # Fallback: show models without resource info
            console.print("\n[bold]Available Whisper Models:[/bold]")
            for model_name in list_models():
                console.print(f"  • {model_name}")
        raise typer.Exit(0)
    
    # Validate input_file is provided when not using --list-models
    if input_file is None:
        console.print("[red]Error:[/red] INPUT_FILE is required when not using --list-models")
        raise typer.Exit(1)
    
    # Build pipeline configuration from CLI arguments
    config = PipelineConfig(
        model=model,
        auto=auto,
        no_gpu=no_gpu,
        model_suffix=model_suffix,
        llm_engine=llm_engine,
        llm_model=llm_model,
        llm_base_url=llm_base_url,
        normalize=normalize,
        repair=repair,
        repair_requested=repair_requested,
        remove_fillers=remove_fillers,
        title=title,
        keep_audio=keep_audio,
        output=output,
        lang=lang,
        notes_mode=notes,
        meeting_type=meeting_type or "auto",
        classify=classify,
        template=template,
        no_interactive=no_interactive,
        verbose=verbose,
    )
    
    # Initialize OutputManager and pipeline context
    try:
        manager = OutputManager(input_file, outdir=outdir)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to initialize output directory: {e}")
        raise typer.Exit(1)
    
    context = PipelineContext(
        input_file=input_file,
        manager=manager,
        process_start_time=datetime.now(),
    )
    
    # Execute the pipeline
    try:
        pipeline = TranscribePipeline(config, context, console=console)
        pipeline.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    from mnemofy import __version__

    console.print(f"mnemofy version {__version__}")


@app.command()
def analyze_metadata(
    metadata_file: Optional[Path] = typer.Argument(
        None,
        help="Path to metadata JSON file (*.metadata.json). If not provided, will also analyze artifacts manifest if found.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    artifacts_file: Optional[Path] = typer.Option(
        None,
        "--artifacts",
        "-a",
        help="Path to artifacts manifest JSON file (*.artifacts.json)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    transcripts: Optional[list[Path]] = typer.Option(
        None,
        "--transcripts",
        "-t",
        help="Path to transcript JSON files to compare (can specify multiple times)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    cost: bool = typer.Option(
        False,
        "--cost",
        "-c",
        help="Include LLM cost estimation",
    ),
) -> None:
    """Analyze processing metadata and artifacts.

    This command analyzes the metadata and artifacts generated during transcription,
    providing insights into model usage, processing time, and output statistics.

    Examples:
        # Analyze metadata file
        mnemofy analyze-metadata meeting.metadata.json

        # Analyze with artifacts manifest
        mnemofy analyze-metadata meeting.metadata.json -a meeting.artifacts.json

        # Compare multiple transcript JSONs
        mnemofy analyze-metadata -t meeting.tiny.transcript.json -t meeting.base.transcript.json

        # Include LLM cost estimation
        mnemofy analyze-metadata meeting.metadata.json --cost
    """
    from mnemofy.analysis import (
        analyze_processing_metadata,
        analyze_artifacts_manifest,
        compare_transcript_metadata,
        calculate_processing_cost,
    )

    if not metadata_file and not artifacts_file and not transcripts:
        console.print("[red]Error: Must provide at least one of: metadata file, artifacts file, or transcript files[/red]")
        raise typer.Exit(1)

    # Analyze metadata
    if metadata_file:
        if not metadata_file.exists():
            console.print(f"[red]Error: Metadata file not found: {metadata_file}[/red]")
            raise typer.Exit(1)
        analyze_processing_metadata(metadata_file)

        # Calculate cost if requested
        if cost:
            calculate_processing_cost(metadata_file)

        # Auto-discover artifacts file if not specified
        if not artifacts_file:
            auto_artifacts = metadata_file.with_suffix(".artifacts.json")
            if auto_artifacts.exists():
                artifacts_file = auto_artifacts

    # Analyze artifacts
    if artifacts_file:
        if not artifacts_file.exists():
            console.print(f"[red]Error: Artifacts file not found: {artifacts_file}[/red]")
            raise typer.Exit(1)
        analyze_artifacts_manifest(artifacts_file)

    # Compare transcripts
    if transcripts:
        valid_transcripts = [t for t in transcripts if t.exists()]
        if len(valid_transcripts) < 2:
            console.print("[yellow]Warning: Need at least 2 transcript files for comparison[/yellow]")
        else:
            compare_transcript_metadata(valid_transcripts)


@app.command()
def compare_runs(
    history_file: Path = typer.Argument(
        ...,
        help="Path to run history file (*.run-history.jsonl)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    show_analysis: bool = typer.Option(
        True,
        "--analysis/--no-analysis",
        help="Show detailed performance analysis",
    ),
    show_recommendations: bool = typer.Option(
        True,
        "--recommendations/--no-recommendations",
        help="Show model recommendations",
    ),
) -> None:
    """Compare transcription runs with different models.

    This command analyzes the run history file to compare performance and quality
    across different model runs, helping you choose the best model for your needs.

    The run history file (*.run-history.jsonl) is automatically created by the
    transcribe command each time you process a file.

    Examples:
        # Compare all runs
        mnemofy compare-runs meeting.run-history.jsonl

        # Show only comparison table, skip analysis
        mnemofy compare-runs meeting.run-history.jsonl --no-analysis

        # Skip recommendations
        mnemofy compare-runs meeting.run-history.jsonl --no-recommendations
    """
    from mnemofy.analysis import (
        load_run_history,
        display_run_comparison,
        analyze_model_performance,
        show_recommendations as show_recommendations_func,
    )

    if not history_file.exists():
        console.print(f"[red]Error: Run history file not found: {history_file}[/red]")
        raise typer.Exit(1)

    # Load run history
    runs = load_run_history(history_file)

    if not runs:
        console.print("[yellow]No valid run records found.[/yellow]")
        raise typer.Exit(0)

    # Display comparison table
    display_run_comparison(runs)

    # Show analysis
    if show_analysis:
        analyze_model_performance(runs)

    # Show recommendations
    if show_recommendations:
        show_recommendations_func(runs)

    console.print(f"\n[dim]Total runs analyzed: {len(runs)}[/dim]")
    console.print(f"[dim]History file: {history_file}[/dim]\n")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
