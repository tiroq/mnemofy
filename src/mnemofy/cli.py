"""Command-line interface for mnemofy."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mnemofy.audio import AudioExtractor
from mnemofy.notes import NoteGenerator
from mnemofy.transcriber import Transcriber

app = typer.Typer(
    name="mnemofy",
    help="Extract audio from media files, transcribe speech, and produce documented meeting notes",
    add_completion=False,
)
console = Console()


@app.command()
def transcribe(
    input_file: Path = typer.Argument(
        ...,
        help="Path to audio or video file (aac, mp3, wav, mkv, mp4)",
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
    model: str = typer.Option(
        "base",
        "--model",
        "-m",
        help="Whisper model to use (tiny, base, small, medium, large)",
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
) -> None:
    """
    Transcribe audio/video file and generate structured meeting notes.

    The tool will:
    1. Extract audio from the media file (if needed)
    2. Transcribe speech using Whisper
    3. Generate structured Markdown notes with topics, decisions, actions, and mentions
    """
    try:
        # Determine output path
        if output is None:
            output = input_file.parent / f"{input_file.stem}_notes.md"

        console.print(f"\n[bold blue]mnemofy[/bold blue] - Processing {input_file.name}")

        # Step 1: Extract audio
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Extracting audio...", total=None)

            extractor = AudioExtractor()
            audio_file = extractor.extract_audio(input_file)

            progress.update(task, description="[green]✓ Audio extracted")

        console.print(f"[dim]Audio file: {audio_file}[/dim]")

        # Step 2: Transcribe
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Transcribing with Whisper ({model})...", total=None
            )

            transcriber = Transcriber(model_name=model)
            transcription = transcriber.transcribe(audio_file)

            progress.update(task, description="[green]✓ Transcription complete")

        # Step 3: Generate notes
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating notes...", total=None)

            generator = NoteGenerator()
            segments = transcriber.get_segments(transcription)
            annotated = generator.annotate_segments(segments)
            markdown = generator.generate_markdown(annotated, title=title)

            # Write output
            output.write_text(markdown, encoding="utf-8")

            progress.update(task, description="[green]✓ Notes generated")

        # Clean up temporary audio file if needed
        if not keep_audio and audio_file != input_file:
            try:
                audio_file.unlink()
            except Exception:
                pass  # Ignore cleanup errors

        console.print(f"\n[bold green]✓ Success![/bold green]")
        console.print(f"[dim]Notes saved to:[/dim] {output}")

        # Show stats
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Segments: {len(segments)}")
        topics = sum(1 for s in annotated if s.is_topic)
        decisions = sum(1 for s in annotated if s.is_decision)
        actions = sum(1 for s in annotated if s.is_action)
        all_mentions = set()
        for s in annotated:
            all_mentions.update(s.mentions)

        if topics > 0:
            console.print(f"  Topics: {topics}")
        if decisions > 0:
            console.print(f"  Decisions: {decisions}")
        if actions > 0:
            console.print(f"  Action items: {actions}")
        if all_mentions:
            console.print(f"  Mentions: {len(all_mentions)}")

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
