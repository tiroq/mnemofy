"""LLM integration module for enhanced classification and notes generation.

Provides pluggable LLM backends (OpenAI-compatible APIs, Ollama) with graceful
fallback to heuristic methods when LLM is unavailable or fails.
"""

from typing import Optional
from mnemofy.llm.base import BaseLLMEngine
from mnemofy.llm.openai_engine import OpenAIEngine
from mnemofy.llm.ollama_engine import OllamaEngine
from mnemofy.llm.config import LLMConfig, get_llm_config


def get_llm_engine(
    engine_type: str = "openai",
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> Optional[BaseLLMEngine]:
    """Factory function to create LLM engine instances with health checks.
    
    Args:
        engine_type: Type of engine ("openai", "ollama", "openai_compat")
        model: Model name (uses defaults if not provided)
        base_url: Custom API endpoint (optional)
        api_key: API key for authenticated endpoints (optional, from env if not provided)
        timeout: Request timeout in seconds
    
    Returns:
        LLM engine instance if healthy, None if unavailable or unhealthy
    
    Examples:
        >>> engine = get_llm_engine("openai")
        >>> if engine:
        ...     result = engine.classify_meeting_type(transcript)
        
        >>> engine = get_llm_engine("ollama", model="llama3.2:3b")
    """
    try:
        # Create engine instance
        if engine_type in ("openai", "openai_compat"):
            engine = OpenAIEngine(
                model=model,
                base_url=base_url,
                api_key=api_key,
                timeout=timeout
            )
        elif engine_type == "ollama":
            engine = OllamaEngine(
                model=model,
                base_url=base_url,
                timeout=timeout
            )
        else:
            return None
        
        # Health check
        if not engine.health_check():
            return None
        
        return engine
        
    except Exception:
        # Any error during creation or health check -> return None for graceful fallback
        return None


__all__ = [
    "BaseLLMEngine",
    "OpenAIEngine",
    "OllamaEngine",
    "LLMConfig",
    "get_llm_config",
    "get_llm_engine",
]
