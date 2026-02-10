"""Base interface for LLM engines."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from mnemofy.classifier import ClassificationResult, GroundedItem


class BaseLLMEngine(ABC):
    """Abstract base class for LLM engines.
    
    All LLM implementations must inherit from this class and implement
    the required methods for classification and notes generation.
    """
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if LLM engine is reachable and operational.
        
        Returns:
            True if engine is healthy, False otherwise
        """
        pass
    
    @abstractmethod
    def classify_meeting_type(
        self,
        transcript_text: str,
        high_signal_segments: Optional[List[str]] = None
    ) -> ClassificationResult:
        """Classify meeting type using LLM reasoning.
        
        Args:
            transcript_text: Full or windowed transcript text
            high_signal_segments: Optional list of high-signal text segments
        
        Returns:
            ClassificationResult with detected type, confidence, evidence
        
        Raises:
            LLMError: If LLM request fails after retries
            ValueError: If LLM returns invalid response
        """
        pass
    
    @abstractmethod
    def generate_notes(
        self,
        transcript_segments: List[Dict[str, Any]],
        meeting_type: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, List[GroundedItem]]:
        """Generate structured notes using LLM extraction.
        
        All extracted items MUST be grounded with transcript references.
        Items that cannot be traced to transcript should be marked as "unclear".
        
        Args:
            transcript_segments: List of segment dicts with start, end, text, speaker
            meeting_type: Detected meeting type for context
            focus_areas: Optional areas to focus extraction on
        
        Returns:
            Dictionary with keys like decisions, actions, mentions, each containing
            lists of GroundedItem objects with transcript references
        
        Raises:
            LLMError: If LLM request fails after retries
            ValueError: If LLM returns ungrounded content
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model being used.
        
        Returns:
            Model name string (e.g., "gpt-4o-mini", "llama3.2:3b")
        """
        pass


class LLMError(Exception):
    """Exception raised when LLM operations fail."""
    pass
