"""Example: Using Model-Aware Artifacts and Metadata

This script demonstrates how to use the new metadata features
to analyze and compare processing results.
"""

import json
from pathlib import Path


def analyze_processing_metadata(metadata_path: Path) -> None:
    """Analyze processing metadata and print summary."""
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    print("=" * 60)
    print("PROCESSING METADATA ANALYSIS")
    print("=" * 60)
    
    # Basic info
    print(f"\nInput File: {metadata['input_file']}")
    print(f"Processing Time: {metadata['duration_seconds']:.2f}s")
    
    # ASR model info
    asr = metadata['asr_engine']
    print(f"\nASR Model: {asr['engine']} / {asr['model']}")
    if asr.get('model_size_gb'):
        print(f"  - Model Size: {asr['model_size_gb']} GB")
        print(f"  - Quality Rating: {asr.get('quality_rating', 'N/A')}/5")
        print(f"  - Speed Rating: {asr.get('speed_rating', 'N/A')}/5")
    
    # LLM model info (if used)
    if metadata.get('llm_engine'):
        llm = metadata['llm_engine']
        print(f"\nLLM Model: {llm['engine']} / {llm['model']}")
        print(f"  - Purpose: {llm['purpose']}")
    
    # Processing config
    config = metadata['config']
    print(f"\nConfiguration:")
    print(f"  - Language: {config['language']}")
    print(f"  - Normalized: {config['normalize']}")
    print(f"  - Repaired: {config['repair']}")
    if config.get('meeting_type'):
        print(f"  - Meeting Type: {config['meeting_type']}")
    
    # Statistics
    print(f"\nTranscript Statistics:")
    print(f"  - Duration: {metadata.get('transcript_duration_seconds', 0):.1f}s")
    print(f"  - Segments: {metadata.get('segment_count', 0)}")
    print(f"  - Words: {metadata.get('word_count', 0)}")


def analyze_artifacts_manifest(manifest_path: Path) -> None:
    """Analyze artifacts manifest and print summary."""
    with open(manifest_path) as f:
        manifest = json.load(f)
    
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


def compare_transcript_metadata(json_paths: list[Path]) -> None:
    """Compare metadata from multiple transcript JSON files."""
    print("\n" + "=" * 60)
    print("TRANSCRIPT COMPARISON")
    print("=" * 60)
    
    metadatas = []
    for path in json_paths:
        with open(path) as f:
            data = json.load(f)
            metadatas.append((path.name, data['metadata']))
    
    print(f"\nComparing {len(metadatas)} transcripts:\n")
    
    # Print comparison table
    headers = ["File", "Model", "Quality", "Speed", "Words", "Segments"]
    print(f"{headers[0]:30} {headers[1]:10} {headers[2]:8} {headers[3]:6} {headers[4]:8} {headers[5]:8}")
    print("-" * 80)
    
    for filename, metadata in metadatas:
        model = metadata.get('model', 'N/A')
        quality = metadata.get('quality_rating', 'N/A')
        speed = metadata.get('speed_rating', 'N/A')
        words = metadata.get('word_count', 0)
        segments = metadata.get('segment_count', 0)
        
        print(f"{filename:30} {model:10} {quality:8} {speed:6} {words:8} {segments:8}")


def calculate_processing_cost(metadata_path: Path) -> None:
    """Estimate LLM processing cost based on usage."""
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    if not metadata.get('llm_engine'):
        print("\nNo LLM usage detected.")
        return
    
    print("\n" + "=" * 60)
    print("LLM COST ESTIMATION")
    print("=" * 60)
    
    llm = metadata['llm_engine']
    word_count = metadata.get('word_count', 0)
    
    # Rough token estimation (words * 1.3 for English)
    estimated_tokens = int(word_count * 1.3)
    
    print(f"\nLLM Model: {llm['model']}")
    print(f"Purpose: {llm['purpose']}")
    print(f"Estimated Input Tokens: ~{estimated_tokens:,}")
    
    # Cost estimation (example rates - adjust based on actual pricing)
    if 'gpt-4o' in llm['model']:
        cost_per_1k = 0.005  # Example rate
        estimated_cost = (estimated_tokens / 1000) * cost_per_1k
        print(f"Estimated Cost: ${estimated_cost:.4f} USD")
    elif 'ollama' in llm['engine']:
        print("Cost: $0.00 (local model)")
    else:
        print("Cost estimation not available for this model")


if __name__ == "__main__":
    # Example usage
    example_dir = Path("examples")
    
    # Analyze processing metadata
    metadata_file = example_dir / "sample.metadata.json"
    if metadata_file.exists():
        analyze_processing_metadata(metadata_file)
    
    # Analyze artifacts manifest
    manifest_file = example_dir / "sample.artifacts.json"
    if manifest_file.exists():
        analyze_artifacts_manifest(manifest_file)
    
    # Compare transcripts from different models
    transcript_files = [
        example_dir / "sample.tiny.transcript.json",
        example_dir / "sample.base.transcript.json",
        example_dir / "sample.small.transcript.json",
    ]
    existing_files = [f for f in transcript_files if f.exists()]
    if len(existing_files) > 1:
        compare_transcript_metadata(existing_files)
    
    # Calculate LLM cost
    if metadata_file.exists():
        calculate_processing_cost(metadata_file)
    
    print("\n" + "=" * 60)
