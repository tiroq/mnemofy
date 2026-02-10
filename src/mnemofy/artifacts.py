"""Artifact generation and metadata management.

This module provides comprehensive artifact metadata tracking and generation,
including processing details, model information, and artifact manifests.
"""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProcessingConfig:
    """Configuration parameters used during processing.
    
    Attributes:
        language: Language code (e.g., 'en', 'es')
        normalize: Whether transcript normalization was applied
        repair: Whether LLM-based repair was applied
        meeting_type: Detected or specified meeting type (e.g., 'status', 'planning')
        classify_mode: Classification method used ('heuristic', 'llm', or 'off')
        notes_mode: Notes generation mode ('basic' or 'llm')
    """
    language: str
    normalize: bool = False
    repair: bool = False
    meeting_type: Optional[str] = None
    classify_mode: str = "heuristic"
    notes_mode: str = "basic"


@dataclass
class ASREngineInfo:
    """Information about the ASR (speech-to-text) engine used.
    
    Attributes:
        engine: Engine name (e.g., 'faster-whisper')
        model: Model name (e.g., 'base', 'small', 'large-v3')
        model_size_gb: Approximate model size in GB
        quality_rating: Quality rating 1-5 (from ModelSpec)
        speed_rating: Speed rating 1-5 (from ModelSpec)
    """
    engine: str
    model: str
    model_size_gb: Optional[float] = None
    quality_rating: Optional[int] = None
    speed_rating: Optional[int] = None


@dataclass
class LLMEngineInfo:
    """Information about the LLM engine used (optional).
    
    Attributes:
        engine: LLM engine type (e.g., 'openai', 'ollama', 'openai_compat')
        model: LLM model name (e.g., 'gpt-4o-mini', 'llama3.2:3b')
        purpose: What the LLM was used for (e.g., 'meeting_type_detection', 'repair')
    """
    engine: str
    model: str
    purpose: str = "general"


@dataclass
class ArtifactInfo:
    """Information about a single generated artifact.
    
    Attributes:
        path: Relative path to the artifact (from project root)
        format: File format (e.g., 'txt', 'srt', 'json', 'md')
        description: Human-readable description
        size_bytes: File size in bytes (set after writing)
        model_used: Model name used to generate (if applicable)
        schema_version: Schema version for structured formats
    """
    path: str
    format: str
    description: str
    size_bytes: Optional[int] = None
    model_used: Optional[str] = None
    schema_version: Optional[str] = None


@dataclass
class ProcessingMetadata:
    """Comprehensive metadata about transcript processing.
    
    Attributes:
        schema_version: Metadata schema version
        input_file: Original input filename
        start_timestamp: ISO format timestamp when processing started
        end_timestamp: ISO format timestamp when processing completed
        duration_seconds: Total processing duration
        asr_engine: Information about ASR engine used
        llm_engine: Optional information about LLM engine used
        config: Processing configuration used
        artifacts: List of generated artifacts
        language_detected: Detected language (may differ from config.language)
        transcript_duration_seconds: Total audio duration transcribed
        word_count: Total word count in transcript
        segment_count: Number of segments in transcript
    """
    schema_version: str = "1.0"
    input_file: str = ""
    start_timestamp: str = ""
    end_timestamp: str = ""
    duration_seconds: float = 0.0
    asr_engine: Optional[ASREngineInfo] = None
    llm_engine: Optional[LLMEngineInfo] = None
    config: Optional[ProcessingConfig] = None
    artifacts: List[ArtifactInfo] = field(default_factory=list)
    language_detected: Optional[str] = None
    transcript_duration_seconds: float = 0.0
    word_count: int = 0
    segment_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, serializing nested dataclasses.
        
        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        data = asdict(self)
        # Ensure timestamps are ISO format strings
        if self.start_timestamp:
            data["start_timestamp"] = self.start_timestamp
        if self.end_timestamp:
            data["end_timestamp"] = self.end_timestamp
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string.
        
        Args:
            indent: JSON indentation level (default: 2).
        
        Returns:
            Pretty-printed JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class ArtifactManifest:
    """Index of all generated artifacts for a processing run.
    
    Attributes:
        schema_version: Manifest schema version
        generated_at: ISO format timestamp of manifest generation
        input_file: Original input filename
        artifacts_by_type: Map of artifact type to list of ArtifactInfo
        total_size_bytes: Total size of all artifacts
        model_name: Name of model(s) used
    """
    schema_version: str = "1.0"
    generated_at: str = ""
    input_file: str = ""
    artifacts_by_type: Dict[str, List[ArtifactInfo]] = field(default_factory=dict)
    total_size_bytes: int = 0
    model_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, serializing nested dataclasses.
        
        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        artifacts_dict = {}
        for artifact_type, artifacts in self.artifacts_by_type.items():
            artifacts_dict[artifact_type] = [asdict(a) for a in artifacts]
        
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "input_file": self.input_file,
            "model_name": self.model_name,
            "artifacts_by_type": artifacts_dict,
            "total_size_bytes": self.total_size_bytes,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string.
        
        Args:
            indent: JSON indentation level (default: 2).
        
        Returns:
            Pretty-printed JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def add_artifact(
        self,
        artifact_type: str,
        path: str,
        format: str,
        description: str,
        size_bytes: Optional[int] = None,
        model_used: Optional[str] = None,
        schema_version: Optional[str] = None,
    ) -> None:
        """Add an artifact to the manifest.
        
        Args:
            artifact_type: Artifact category (e.g., 'transcript', 'notes', 'metadata')
            path: Relative path to artifact
            format: File format/extension
            description: Human-readable description
            size_bytes: Optional file size
            model_used: Optional model name
            schema_version: Optional schema version
        """
        if artifact_type not in self.artifacts_by_type:
            self.artifacts_by_type[artifact_type] = []
        
        artifact = ArtifactInfo(
            path=path,
            format=format,
            description=description,
            size_bytes=size_bytes,
            model_used=model_used,
            schema_version=schema_version,
        )
        
        self.artifacts_by_type[artifact_type].append(artifact)
        
        if size_bytes:
            self.total_size_bytes += size_bytes


def create_processing_metadata(
    input_file: str,
    asr_engine: ASREngineInfo,
    config: ProcessingConfig,
    start_time: datetime,
    end_time: datetime,
    llm_engine: Optional[LLMEngineInfo] = None,
    **kwargs: Any,
) -> ProcessingMetadata:
    """Factory function to create ProcessingMetadata.
    
    Args:
        input_file: Input filename
        asr_engine: Information about ASR engine
        config: Processing configuration
        start_time: Processing start time
        end_time: Processing end time
        llm_engine: Optional LLM engine information
        **kwargs: Additional fields to set on metadata object
                 (language_detected, transcript_duration_seconds, word_count, etc.)
    
    Returns:
        Fully initialized ProcessingMetadata object
    """
    duration = (end_time - start_time).total_seconds()
    
    metadata = ProcessingMetadata(
        input_file=input_file,
        asr_engine=asr_engine,
        config=config,
        llm_engine=llm_engine,
        start_timestamp=start_time.isoformat(),
        end_timestamp=end_time.isoformat(),
        duration_seconds=duration,
    )
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(metadata, key):
            setattr(metadata, key, value)
    
    return metadata


def create_artifact_manifest(
    input_file: str,
    model_name: Optional[str] = None,
) -> ArtifactManifest:
    """Factory function to create ArtifactManifest.
    
    Args:
        input_file: Input filename
        model_name: Optional model name
    
    Returns:
        Newly initialized ArtifactManifest object
    """
    return ArtifactManifest(
        generated_at=datetime.now().isoformat(),
        input_file=input_file,
        model_name=model_name,
    )
