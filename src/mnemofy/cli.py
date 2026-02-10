"""Command-line interface for mnemofy."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.audio import AudioExtractor
from mnemofy.classifier import HeuristicClassifier, MeetingType, extract_high_signal_segments
from mnemofy.formatters import TranscriptFormatter
from mnemofy.llm import get_llm_engine, get_llm_config
from mnemofy.llm.base import LLMError
from mnemofy.model_selector import (
    ModelSelectionError,
    get_model_table,
    list_models,
    recommend_model,
)
from mnemofy.notes import (
    StructuredNotesGenerator,
    BasicNotesExtractor,
    render_meeting_notes,
)
from mnemofy.output_manager import OutputManager
from mnemofy.resources import detect_system_resources
from mnemofy.transcriber import Transcriber
from mnemofy.tui.model_menu import ModelMenu, is_interactive_environment

app = typer.Typer(
    name="mnemofy",
    help="Extract audio from media files, transcribe speech, and produce documented meeting notes",
    add_completion=False,
)
console = Console()


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
    import logging
    
    # Handle --list-models flag (exit early)
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
    
    # Model selection flow
    selected_model = None
    
    # Step 1: Check for explicit model override
    if model is not None:
        selected_model = model
        console.print(f"[dim]Using explicit model: {selected_model}[/dim]")
    else:
        # Step 2: Detect system resources for auto-selection
        try:
            resources = detect_system_resources()
            use_gpu = not no_gpu
            
            # Step 3: Determine if interactive menu should be shown
            interactive_available = is_interactive_environment()
            should_show_menu = interactive_available and not auto
            
            if should_show_menu:
                # Interactive mode: show menu for user selection
                from mnemofy.model_selector import filter_compatible_models
                
                compatible = filter_compatible_models(resources, use_gpu=use_gpu)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                
                console.print(f"\n[bold]System Resources:[/bold] {reasoning}")
                console.print("[bold]Select a model:[/bold]")
                
                menu = ModelMenu(compatible, recommended=recommended, resources=resources)
                selected_spec = menu.show()
                
                if selected_spec is None:
                    console.print("[yellow]Model selection cancelled[/yellow]")
                    raise typer.Exit(1)
                
                selected_model = selected_spec.name
                console.print(f"[dim]Selected model: {selected_model}[/dim]")
            else:
                # Auto-selection mode (--auto or non-TTY)
                recommended, reasoning = recommend_model(resources, use_gpu=use_gpu)
                selected_model = recommended.name
                mode = "auto-selected"
                console.print(f"[dim]{mode.capitalize()}: {recommended.name} ({reasoning})[/dim]")
                
        except ModelSelectionError as e:
            # No compatible models found - this is a critical error
            console.print(f"[red]Error:[/red] {e}")
            console.print("[red]No compatible models found for your system.[/red]")
            console.print("\nPossible solutions:")
            console.print("  • Free up more RAM and try again")
            console.print("  • Manually specify a smaller model with --model tiny")
            console.print("  • Use --no-gpu to force CPU-only mode")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Resource detection failed: {e}")
            console.print("[yellow]Falling back to 'base' model[/yellow]")
            selected_model = "base"
    
    try:
        # Initialize OutputManager for path management
        try:
            manager = OutputManager(input_file, outdir=outdir)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to initialize output directory: {e}")
            raise typer.Exit(1)

        console.print(f"\n[bold blue]mnemofy[/bold blue] - Processing {input_file.name}")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting audio...", total=None)

            # Use OutputManager to determine audio output path
            audio_output_path = manager.get_audio_path()
            extractor = AudioExtractor()
            audio_file = extractor.extract_audio(input_file, output_file=audio_output_path)

            progress.update(task, description="[green]✓ Audio extracted")

        console.print(f"[dim]Audio file: {audio_file}[/dim]")

        # Step 3: Generate formatted transcripts
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating formatted transcripts...", total=None)

            transcriber = Transcriber(model_name=selected_model)
            transcription = transcriber.transcribe(audio_file, language=lang)
            segments = transcriber.get_segments(transcription)
            
            # Determine effective language: prefer explicit --lang, then detected, then fallback
            detected_language = transcription.get("language") if transcription else None
            effective_language = lang or detected_language or "en"
            
            # Prepare metadata
            metadata = {
                "engine": "faster-whisper",
                "model": selected_model,
                "language": effective_language,
                "duration": sum(s["end"] - s["start"] for s in segments),
            }
            
            # Generate all formats
            txt_output = TranscriptFormatter.to_txt(segments)
            srt_output = TranscriptFormatter.to_srt(segments)
            json_output = TranscriptFormatter.to_json(segments, metadata)
            
            # Write transcript files
            txt_path = manager.get_transcript_paths()["txt"]
            srt_path = manager.get_transcript_paths()["srt"]
            json_path = manager.get_transcript_paths()["json"]
            
            txt_path.write_text(txt_output, encoding="utf-8")
            srt_path.write_text(srt_output, encoding="utf-8")
            json_path.write_text(json_output, encoding="utf-8")

            progress.update(task, description="[green]✓ Transcripts generated")

        # Step 4: Detect meeting type (if enabled)
        classification_result = None
        detected_type = None
        llm_engine_instance = None
        
        # Initialize LLM engine if LLM mode requested
        if classify == "llm" or notes == "llm":
            try:
                # Load configuration from file + env + CLI overrides
                cli_overrides = {}
                if llm_engine != "openai":  # Only override if not default
                    cli_overrides["engine"] = llm_engine
                if llm_model:
                    cli_overrides["model"] = llm_model
                if llm_base_url:
                    cli_overrides["base_url"] = llm_base_url
                
                llm_config = get_llm_config(cli_overrides=cli_overrides)
                
                # Create LLM engine using merged config
                llm_engine_instance = get_llm_engine(
                    engine_type=llm_config.engine,
                    model=llm_config.model,
                    base_url=llm_config.base_url,
                    api_key=llm_config.api_key,
                    timeout=llm_config.timeout
                )
                
                if llm_engine_instance:
                    console.print(f"[dim]LLM engine: {llm_engine_instance.get_model_name()}[/dim]")
                else:
                    console.print("[yellow]Warning:[/yellow] LLM engine unavailable, falling back to heuristic mode")
            except Exception as e:
                console.print(f"[yellow]Warning:[/yellow] LLM initialization failed: {e}")
                console.print("[dim]Falling back to heuristic mode[/dim]")
        
        if classify != "off" and meeting_type == "auto":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Detecting meeting type...", total=None)
                
                if classify == "llm" and llm_engine_instance:
                    # Use LLM classifier
                    try:
                        transcript_text = " ".join(s["text"] for s in segments)
                        
                        # Extract high-signal segments (use config values if available)
                        llm_config_for_extract = get_llm_config()
                        high_signal = extract_high_signal_segments(
                            transcript_text,
                            context_words=llm_config_for_extract.context_words,
                            max_segments=llm_config_for_extract.max_segments
                        )
                        
                        classification_result = llm_engine_instance.classify_meeting_type(
                            transcript_text,
                            high_signal_segments=high_signal
                        )
                        detected_type = classification_result.detected_type
                        
                        # Display detection result
                        confidence_pct = classification_result.confidence * 100
                        console.print(f"\n[bold]Detected Meeting Type:[/bold] {detected_type.value}")
                        console.print(f"[dim]Confidence: {confidence_pct:.1f}% (LLM)[/dim]")
                        if classification_result.evidence:
                            console.print(f"[dim]Evidence: {', '.join(classification_result.evidence[:3])}[/dim]")
                        
                        progress.update(task, description="[green]✓ Meeting type detected (LLM)")
                    except LLMError as e:
                        console.print(f"[yellow]Warning:[/yellow] LLM classification failed: {e}")
                        console.print("[dim]Falling back to heuristic mode[/dim]")
                        # Fallback to heuristic
                        transcript_text = " ".join(s["text"] for s in segments)
                        classifier = HeuristicClassifier()
                        classification_result = classifier.detect_meeting_type(transcript_text, segments)
                        detected_type = classification_result.detected_type
                        progress.update(task, description="[green]✓ Meeting type detected (heuristic fallback)")
                else:
                    # Use heuristic classifier
                    transcript_text = " ".join(s["text"] for s in segments)
                    classifier = HeuristicClassifier()
                    classification_result = classifier.detect_meeting_type(transcript_text, segments)
                    detected_type = classification_result.detected_type
                    
                    # Display detection result
                    confidence_pct = classification_result.confidence * 100
                    console.print(f"\n[bold]Detected Meeting Type:[/bold] {detected_type.value}")
                    console.print(f"[dim]Confidence: {confidence_pct:.1f}%[/dim]")
                    if classification_result.evidence:
                        console.print(f"[dim]Evidence: {', '.join(classification_result.evidence[:3])}[/dim]")
                    
                    progress.update(task, description="[green]✓ Meeting type detected
                    # Display detection result
                    confidence_pct = classification_result.confidence * 100
                    console.print(f"\n[bold]Detected Meeting Type:[/bold] {detected_type.value}")
                    console.print(f"[dim]Confidence: {confidence_pct:.1f}%[/dim]")
                    if classification_result.evidence:
                        console.print(f"[dim]Evidence: {', '.join(classification_result.evidence[:3])}[/dim]")
                    
                    progress.update(task, description="[green]✓ Meeting type detected")
                elif classify == "llm":
                    console.print("[yellow]LLM classification not yet implemented, falling back to heuristic[/yellow]")
                    transcript_text = " ".join(s["text"] for s in segments)
                    classifier = HeuristicClassifier()
                    classification_result = classifier.detect_meeting_type(transcript_text, segments)
                    detected_type = classification_result.detected_type
                    progress.update(task, description="[green]✓ Meeting type detected (heuristic fallback)")
        elif meeting_type != "auto":
            # Use explicit meeting type
            try:
                detected_type = MeetingType(meeting_type.lower())
                console.print(f"\n[dim]Using explicit meeting type: {detected_type.value}[/dim]")
            except ValueError:
                console.print(f"[red]Error:[/red] Invalid meeting type '{meeting_type}'")
                console.print(f"Valid types: {', '.join(mt.value for mt in MeetingType)}")
                raise typer.Exit(1)
        
        # Step 5: Generate notes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating notes...", total=None)

            # Use meeting-type-aware notes generation if type detected
            if detected_type and not template:
                # Extract structured information (basic or LLM)
                if notes == "llm" and llm_engine_instance:
                    try:
                        # Use LLM notes extraction
                        extracted_items = llm_engine_instance.generate_notes(
                            transcript_segments=segments,
                            meeting_type=detected_type.value,
                            focus_areas=None
                        )
                        console.print("[dim]Notes extracted using LLM[/dim]")
                    except LLMError as e:
                        console.print(f"[yellow]Warning:[/yellow] LLM notes extraction failed: {e}")
                        console.print("[dim]Falling back to basic extraction[/dim]")
                        # Fallback to basic extraction
                        extractor = BasicNotesExtractor()
                        extracted_items = extractor.extract_all(segments, detected_type)
                else:
                    # Use basic heuristic extraction
                    extractor = BasicNotesExtractor()
                    extracted_items = extractor.extract_all(segments, detected_type)
                
                # Prepare metadata for template
                template_metadata = {
                    "title": title,
                    "date": metadata.get("date", ""),
                    "duration": f"{int(metadata['duration'] // 60)}m {int(metadata['duration'] % 60)}s",
                    "confidence": f"{classification_result.confidence:.2f}" if classification_result else "N/A",
                    "engine": classification_result.engine if classification_result else "manual",
                }
                
                # Render using appropriate template
                notes_markdown = render_meeting_notes(
                    detected_type,
                    extracted_items,
                    template_metadata,
                    custom_template_dir=template.parent if template else None
                )
            else:
                # Fall back to legacy notes generator
                try:
                    notes_generator = StructuredNotesGenerator(mode="basic")  # Only basic mode supported in legacy
                    notes_markdown = notes_generator.generate(segments, metadata, include_audio=keep_audio)
                except NotImplementedError as e:
                    console.print(f"[red]Error: {e}[/red]")
                    console.print("[yellow]Please specify a meeting type to use LLM notes generation.[/yellow]")
                    raise typer.Exit(1)
            
            # Determine output path for notes
            if output is None:
                output = manager.get_notes_path()
            
            # Write notes output
            output.write_text(notes_markdown, encoding="utf-8")
            
            # Write meeting-type.json if type was detected
            if classification_result:
                import json
                meeting_type_path = manager.outdir / f"{manager.base_name}.meeting-type.json"
                meeting_type_data = {
                    "detected_type": classification_result.detected_type.value,
                    "confidence": classification_result.confidence,
                    "evidence": classification_result.evidence,
                    "secondary_types": [
                        {"type": mt.value, "score": score}
                        for mt, score in classification_result.secondary_types
                    ],
                    "engine": classification_result.engine,
                    "timestamp": classification_result.timestamp.isoformat(),
                }
                meeting_type_path.write_text(json.dumps(meeting_type_data, indent=2), encoding="utf-8")

            progress.update(task, description="[green]✓ Notes generated")

        # Clean up temporary audio file if needed
        if not keep_audio and audio_file != input_file:
            try:
                audio_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        console.print("\n[bold green]✓ Success![/bold green]")
        console.print(f"[dim]Output files generated:[/dim]")
        console.print(f"  Transcript (TXT): {txt_path}")
        console.print(f"  Subtitle (SRT): {srt_path}")
        console.print(f"  Structured (JSON): {json_path}")
        if classification_result:
            meeting_type_path = manager.outdir / f"{manager.base_name}.meeting-type.json"
            console.print(f"  Meeting Type: {meeting_type_path}")
        console.print(f"  Notes: {output}")

        # Show stats
        console.print("\n[bold]Statistics:[/bold]")
        console.print(f"  Segments: {len(segments)}")
        total_duration = sum(s.end - s.start for s in segments)
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        console.print(f"  Duration: {minutes}m {seconds}s")

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


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
