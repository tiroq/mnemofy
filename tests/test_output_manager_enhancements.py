"""Tests for OutputManager metadata and model-aware path enhancements."""

import tempfile
from pathlib import Path

import pytest

from mnemofy.output_manager import OutputManager


@pytest.fixture
def temp_input_file():
    """Create a temporary input file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        temp_path = Path(f.name)
        temp_path.write_text("test content")
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_outdir():
    """Create a temporary output directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    yield temp_dir
    
    # Cleanup
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_get_metadata_path(temp_input_file, temp_outdir):
    """Test metadata path generation."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    metadata_path = manager.get_metadata_path()
    
    expected_name = f"{temp_input_file.stem}.metadata.json"
    assert metadata_path.name == expected_name
    assert metadata_path.parent == temp_outdir


def test_get_artifacts_manifest_path(temp_input_file, temp_outdir):
    """Test artifacts manifest path generation."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    manifest_path = manager.get_artifacts_manifest_path()
    
    expected_name = f"{temp_input_file.stem}.artifacts.json"
    assert manifest_path.name == expected_name
    assert manifest_path.parent == temp_outdir


def test_get_model_aware_transcript_paths_without_model(temp_input_file, temp_outdir):
    """Test model-aware paths without model name (standard paths)."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    paths = manager.get_model_aware_transcript_paths()
    
    # Should be identical to get_transcript_paths() when model_name is None
    standard_paths = manager.get_transcript_paths()
    
    assert paths == standard_paths
    assert paths["txt"].name == f"{temp_input_file.stem}.transcript.txt"
    assert paths["srt"].name == f"{temp_input_file.stem}.transcript.srt"
    assert paths["json"].name == f"{temp_input_file.stem}.transcript.json"


def test_get_model_aware_transcript_paths_with_model(temp_input_file, temp_outdir):
    """Test model-aware paths with model name."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    paths = manager.get_model_aware_transcript_paths(model_name="base")
    
    basename = temp_input_file.stem
    assert paths["txt"].name == f"{basename}.base.transcript.txt"
    assert paths["srt"].name == f"{basename}.base.transcript.srt"
    assert paths["json"].name == f"{basename}.base.transcript.json"
    
    # All paths should be in outdir
    for path in paths.values():
        assert path.parent == temp_outdir


def test_get_model_aware_transcript_paths_different_models(temp_input_file, temp_outdir):
    """Test model-aware paths with different model names."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    
    base_paths = manager.get_model_aware_transcript_paths(model_name="base")
    small_paths = manager.get_model_aware_transcript_paths(model_name="small")
    large_paths = manager.get_model_aware_transcript_paths(model_name="large-v3")
    
    basename = temp_input_file.stem
    
    # Each model should have unique paths
    assert base_paths["txt"].name == f"{basename}.base.transcript.txt"
    assert small_paths["txt"].name == f"{basename}.small.transcript.txt"
    assert large_paths["txt"].name == f"{basename}.large-v3.transcript.txt"
    
    # Paths should be different
    assert base_paths != small_paths
    assert base_paths != large_paths
    assert small_paths != large_paths


def test_metadata_and_manifest_paths_in_outdir(temp_input_file, temp_outdir):
    """Test that metadata and manifest paths respect outdir."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    
    metadata_path = manager.get_metadata_path()
    manifest_path = manager.get_artifacts_manifest_path()
    
    assert metadata_path.parent == temp_outdir
    assert manifest_path.parent == temp_outdir


def test_all_paths_have_consistent_basename(temp_input_file, temp_outdir):
    """Test that all generated paths use consistent basename."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    basename = temp_input_file.stem
    
    # Standard paths
    assert manager.get_audio_path().stem.startswith(basename)
    assert manager.get_notes_path().stem.startswith(basename)
    assert manager.get_changes_log_path().stem.startswith(basename)
    assert manager.get_metadata_path().stem.startswith(basename)
    assert manager.get_artifacts_manifest_path().stem.startswith(basename)
    
    # Transcript paths
    for path in manager.get_transcript_paths().values():
        assert path.stem.startswith(basename)
    
    # Model-aware transcript paths
    for path in manager.get_model_aware_transcript_paths("base").values():
        assert basename in path.stem


def test_metadata_path_default_outdir(temp_input_file):
    """Test metadata path with default outdir (same as input)."""
    manager = OutputManager(temp_input_file)
    metadata_path = manager.get_metadata_path()
    
    # Should be in same directory as input file
    assert metadata_path.parent == temp_input_file.parent
    assert metadata_path.name == f"{temp_input_file.stem}.metadata.json"


def test_model_aware_paths_preserve_extension_format(temp_input_file, temp_outdir):
    """Test that model-aware paths preserve correct extension patterns."""
    manager = OutputManager(temp_input_file, outdir=temp_outdir)
    paths = manager.get_model_aware_transcript_paths("medium")
    
    # Pattern should be: {basename}.{model}.transcript.{ext}
    assert paths["txt"].suffix == ".txt"
    assert paths["srt"].suffix == ".srt"
    assert paths["json"].suffix == ".json"
    
    # Each should contain model name before "transcript"
    assert ".medium.transcript.txt" in paths["txt"].name
    assert ".medium.transcript.srt" in paths["srt"].name
    assert ".medium.transcript.json" in paths["json"].name
