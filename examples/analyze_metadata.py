"""Example: Using Model-Aware Artifacts and Metadata

This script demonstrates how to use the new metadata features
to analyze and compare processing results.

NOTE: These functions are now available as CLI commands:
    mnemofy analyze-metadata <metadata-file>
    mnemofy analyze-metadata --help

This example shows how to use the analysis module programmatically.
"""

from pathlib import Path

# Import analysis functions from mnemofy
from mnemofy.analysis import (
    analyze_processing_metadata,
    analyze_artifacts_manifest,
    compare_transcript_metadata,
    calculate_processing_cost,
)


if __name__ == "__main__":
    # Example usage - same functionality now available via CLI:
    # $ mnemofy analyze-metadata examples/sample.metadata.json --cost
    
    example_dir = Path("examples")
    
    # Analyze processing metadata (use_rich=False for plain text output)
    metadata_file = example_dir / "sample.metadata.json"
    if metadata_file.exists():
        analyze_processing_metadata(metadata_file, use_rich=False)
    
    # Analyze artifacts manifest
    manifest_file = example_dir / "sample.artifacts.json"
    if manifest_file.exists():
        analyze_artifacts_manifest(manifest_file, use_rich=False)
    
    # Compare transcripts from different models
    transcript_files = [
        example_dir / "sample.tiny.transcript.json",
        example_dir / "sample.base.transcript.json",
        example_dir / "sample.small.transcript.json",
    ]
    existing_files = [f for f in transcript_files if f.exists()]
    if len(existing_files) > 1:
        compare_transcript_metadata(existing_files, use_rich=False)
    
    # Calculate LLM cost
    if metadata_file.exists():
        calculate_processing_cost(metadata_file, use_rich=False)
    
    print("\n" + "=" * 60)
    print("\nTIP: Use the CLI for easier access:")
    print("  mnemofy analyze-metadata examples/sample.metadata.json --cost")
