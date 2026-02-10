"""Tests for artifact metadata generation."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from mnemofy.artifacts import (
    ProcessingMetadata,
    ASREngineInfo,
    LLMEngineInfo,
    ProcessingConfig,
    ArtifactManifest,
    ArtifactInfo,
    create_processing_metadata,
    create_artifact_manifest,
)


def test_asr_engine_info_creation():
    """Test ASREngineInfo dataclass creation."""
    asr_info = ASREngineInfo(
        engine="faster-whisper",
        model="base",
        model_size_gb=1.5,
        quality_rating=3,
        speed_rating=5,
    )
    
    assert asr_info.engine == "faster-whisper"
    assert asr_info.model == "base"
    assert asr_info.model_size_gb == 1.5
    assert asr_info.quality_rating == 3
    assert asr_info.speed_rating == 5


def test_llm_engine_info_creation():
    """Test LLMEngineInfo dataclass creation."""
    llm_info = LLMEngineInfo(
        engine="openai",
        model="gpt-4o-mini",
        purpose="meeting_type_detection",
    )
    
    assert llm_info.engine == "openai"
    assert llm_info.model == "gpt-4o-mini"
    assert llm_info.purpose == "meeting_type_detection"


def test_processing_config_creation():
    """Test ProcessingConfig dataclass creation."""
    config = ProcessingConfig(
        language="en",
        normalize=True,
        repair=False,
        meeting_type="status",
        classify_mode="heuristic",
        notes_mode="basic",
    )
    
    assert config.language == "en"
    assert config.normalize is True
    assert config.repair is False
    assert config.meeting_type == "status"
    assert config.classify_mode == "heuristic"
    assert config.notes_mode == "basic"


def test_artifact_info_creation():
    """Test ArtifactInfo dataclass creation."""
    artifact = ArtifactInfo(
        path="meeting.transcript.json",
        format="json",
        description="Structured JSON transcript",
        size_bytes=1024,
        model_used="base",
        schema_version="1.0",
    )
    
    assert artifact.path == "meeting.transcript.json"
    assert artifact.format == "json"
    assert artifact.size_bytes == 1024
    assert artifact.model_used == "base"


def test_processing_metadata_to_dict():
    """Test ProcessingMetadata serialization to dict."""
    asr_info = ASREngineInfo(engine="faster-whisper", model="base")
    config = ProcessingConfig(language="en")
    
    metadata = ProcessingMetadata(
        input_file="meeting.mp4",
        start_timestamp="2026-02-10T10:00:00",
        end_timestamp="2026-02-10T10:05:00",
        duration_seconds=300.0,
        asr_engine=asr_info,
        config=config,
        transcript_duration_seconds=280.5,
        word_count=1500,
        segment_count=45,
    )
    
    data = metadata.to_dict()
    
    assert data["input_file"] == "meeting.mp4"
    assert data["duration_seconds"] == 300.0
    assert data["asr_engine"]["engine"] == "faster-whisper"
    assert data["config"]["language"] == "en"
    assert data["word_count"] == 1500


def test_processing_metadata_to_json():
    """Test ProcessingMetadata JSON serialization."""
    asr_info = ASREngineInfo(engine="faster-whisper", model="small")
    config = ProcessingConfig(language="es", normalize=True)
    
    metadata = ProcessingMetadata(
        input_file="meeting.mp4",
        start_timestamp="2026-02-10T10:00:00",
        end_timestamp="2026-02-10T10:05:00",
        duration_seconds=300.0,
        asr_engine=asr_info,
        config=config,
    )
    
    json_str = metadata.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["schema_version"] == "1.0"
    assert parsed["input_file"] == "meeting.mp4"
    assert parsed["asr_engine"]["model"] == "small"
    assert parsed["config"]["normalize"] is True


def test_create_processing_metadata_factory():
    """Test create_processing_metadata factory function."""
    asr_info = ASREngineInfo(engine="faster-whisper", model="base")
    config = ProcessingConfig(language="en")
    start_time = datetime.fromisoformat("2026-02-10T10:00:00")
    end_time = datetime.fromisoformat("2026-02-10T10:05:00")
    
    metadata = create_processing_metadata(
        input_file="test.mp4",
        asr_engine=asr_info,
        config=config,
        start_time=start_time,
        end_time=end_time,
        word_count=1000,
        segment_count=30,
    )
    
    assert metadata.input_file == "test.mp4"
    assert metadata.duration_seconds == 300.0  # 5 minutes
    assert metadata.word_count == 1000
    assert metadata.segment_count == 30


def test_create_processing_metadata_with_llm():
    """Test create_processing_metadata with LLM engine."""
    asr_info = ASREngineInfo(engine="faster-whisper", model="base")
    llm_info = LLMEngineInfo(engine="openai", model="gpt-4o-mini", purpose="notes_generation")
    config = ProcessingConfig(language="en", notes_mode="llm")
    start_time = datetime.fromisoformat("2026-02-10T10:00:00")
    end_time = datetime.fromisoformat("2026-02-10T10:05:00")
    
    metadata = create_processing_metadata(
        input_file="test.mp4",
        asr_engine=asr_info,
        config=config,
        start_time=start_time,
        end_time=end_time,
        llm_engine=llm_info,
    )
    
    assert metadata.llm_engine is not None
    assert metadata.llm_engine.engine == "openai"
    assert metadata.llm_engine.model == "gpt-4o-mini"


def test_artifact_manifest_creation():
    """Test ArtifactManifest creation."""
    manifest = create_artifact_manifest(
        input_file="meeting.mp4",
        model_name="base",
    )
    
    assert manifest.input_file == "meeting.mp4"
    assert manifest.model_name == "base"
    assert manifest.total_size_bytes == 0
    assert len(manifest.artifacts_by_type) == 0


def test_artifact_manifest_add_artifact():
    """Test adding artifacts to manifest."""
    manifest = create_artifact_manifest("meeting.mp4", "base")
    
    manifest.add_artifact(
        artifact_type="transcript",
        path="meeting.transcript.json",
        format="json",
        description="Structured transcript",
        size_bytes=2048,
        model_used="base",
        schema_version="1.0",
    )
    
    assert "transcript" in manifest.artifacts_by_type
    assert len(manifest.artifacts_by_type["transcript"]) == 1
    assert manifest.total_size_bytes == 2048
    
    artifact = manifest.artifacts_by_type["transcript"][0]
    assert artifact.path == "meeting.transcript.json"
    assert artifact.model_used == "base"


def test_artifact_manifest_multiple_types():
    """Test manifest with multiple artifact types."""
    manifest = create_artifact_manifest("meeting.mp4", "small")
    
    manifest.add_artifact("transcript", "meeting.transcript.txt", "txt", "Plain text", 1024)
    manifest.add_artifact("transcript", "meeting.transcript.json", "json", "JSON", 2048)
    manifest.add_artifact("notes", "meeting.notes.md", "md", "Notes", 512)
    
    assert len(manifest.artifacts_by_type) == 2
    assert len(manifest.artifacts_by_type["transcript"]) == 2
    assert len(manifest.artifacts_by_type["notes"]) == 1
    assert manifest.total_size_bytes == 3584  # 1024 + 2048 + 512


def test_artifact_manifest_to_json():
    """Test ArtifactManifest JSON serialization."""
    manifest = create_artifact_manifest("test.mp4", "base")
    manifest.add_artifact("transcript", "test.transcript.json", "json", "Transcript", 1024, "base")
    
    json_str = manifest.to_json()
    parsed = json.loads(json_str)
    
    assert parsed["schema_version"] == "1.0"
    assert parsed["input_file"] == "test.mp4"
    assert parsed["model_name"] == "base"
    assert parsed["total_size_bytes"] == 1024
    assert "transcript" in parsed["artifacts_by_type"]
    assert len(parsed["artifacts_by_type"]["transcript"]) == 1


def test_artifact_manifest_to_dict():
    """Test ArtifactManifest dict conversion."""
    manifest = create_artifact_manifest("test.mp4", "base")
    manifest.add_artifact("notes", "test.notes.md", "md", "Notes", 512)
    
    data = manifest.to_dict()
    
    assert isinstance(data, dict)
    assert data["input_file"] == "test.mp4"
    assert data["model_name"] == "base"
    assert "notes" in data["artifacts_by_type"]
    assert isinstance(data["artifacts_by_type"]["notes"], list)
