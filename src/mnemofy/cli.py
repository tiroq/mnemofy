"""Command-line interface for mnemofy."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.audio import AudioExtractor
from mnemofy.formatters import TranscriptFormatter
from mnemofy.model_selector import (
    ModelSelectionError,
    get_model_table,
    list_models,
    recommend_model,
)
from mnemofy.notes import NoteGenerator, StructuredNotesGenerator
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
        help="Notes generation mode: 'basic' (deterministic) or 'llm' (LLM-enhanced, future feature)",
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
            transcription = transcriber.transcribe(audio_file)
            segments = transcriber.get_segments(transcription)
            
            # Prepare metadata
            metadata = {
                "engine": "faster-whisper",
                "model": selected_model,
                "language": lang or "en",
                "duration": sum(s.end - s.start for s in segments),
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

        # Step 4: Generate notes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating notes...", total=None)

            # Use enhanced notes generator instead of legacy implementation
            notes_generator = StructuredNotesGenerator(mode=notes)
            notes_markdown = notes_generator.generate(segments, metadata)
            
            # Determine output path for notes
            if output is None:
                output = manager.get_notes_path()
            
            # Write output
            output.write_text(notes_markdown, encoding="utf-8")

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
