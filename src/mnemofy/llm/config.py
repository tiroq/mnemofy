"""Configuration management for LLM settings."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for Python <3.11


@dataclass
class LLMConfig:
    """LLM configuration settings.
    
    Priority (highest to lowest):
    1. CLI flags (explicit overrides)
    2. Environment variables
    3. User config file (~/.config/mnemofy/config.toml)
    4. Default values
    """
    
    # Engine settings
    engine: str = "openai"  # openai, ollama, openai_compat
    model: Optional[str] = None  # None = use engine default
    base_url: Optional[str] = None
    
    # API authentication (must come from environment for security)
    api_key: Optional[str] = field(default=None, repr=False)  # Hide from repr
    
    # Request settings
    timeout: int = 30
    max_retries: int = 2
    
    # Feature flags
    enabled: bool = False  # LLM features enabled by default?
    fallback_to_heuristic: bool = True
    
    # High-signal extraction
    context_words: int = 50
    max_segments: int = 10


def load_config_file(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from TOML file.
    
    Args:
        config_path: Explicit config file path, or None to use default location
    
    Returns:
        Dictionary of configuration values (empty dict if file not found)
    """
    if config_path is None:
        # Default config locations (in priority order)
        candidates = [
            Path.home() / ".config" / "mnemofy" / "config.toml",
            Path.home() / ".mnemofy" / "config.toml",
            Path.cwd() / ".mnemofy.toml",
        ]
        config_path = next((p for p in candidates if p.exists()), None)
    
    if config_path is None or not config_path.exists():
        return {}
    
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("llm", {})
    except Exception:
        # Silently ignore config file errors (use defaults)
        return {}


def load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Environment variables:
    - MNEMOFY_LLM_ENGINE
    - MNEMOFY_LLM_MODEL
    - MNEMOFY_LLM_BASE_URL
    - MNEMOFY_LLM_TIMEOUT
    - MNEMOFY_LLM_ENABLED
    - OPENAI_API_KEY (standard OpenAI env var)
    - OLLAMA_HOST (standard Ollama env var)
    
    Returns:
        Dictionary of configuration values from environment
    """
    config = {}
    
    # Engine settings
    if engine := os.getenv("MNEMOFY_LLM_ENGINE"):
        config["engine"] = engine
    
    if model := os.getenv("MNEMOFY_LLM_MODEL"):
        config["model"] = model
    
    if base_url := os.getenv("MNEMOFY_LLM_BASE_URL"):
        config["base_url"] = base_url
    elif ollama_host := os.getenv("OLLAMA_HOST"):
        # Support standard Ollama environment variable
        config["base_url"] = ollama_host
    
    # API key (security: MUST come from environment, never from config file)
    if api_key := os.getenv("OPENAI_API_KEY"):
        config["api_key"] = api_key
    
    # Request settings
    if timeout := os.getenv("MNEMOFY_LLM_TIMEOUT"):
        try:
            config["timeout"] = int(timeout)
        except ValueError:
            pass
    
    # Feature flags
    if enabled := os.getenv("MNEMOFY_LLM_ENABLED"):
        config["enabled"] = enabled.lower() in ("true", "1", "yes", "on")
    
    return config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple config dictionaries (later configs override earlier ones)."""
    merged = {}
    for config in configs:
        merged.update({k: v for k, v in config.items() if v is not None})
    return merged


def get_llm_config(
    config_file: Optional[Path] = None,
    cli_overrides: Optional[Dict[str, Any]] = None
) -> LLMConfig:
    """Get merged LLM configuration from all sources.
    
    Priority (highest to lowest):
    1. CLI overrides (explicit user flags)
    2. Environment variables
    3. Config file
    4. Defaults
    
    Args:
        config_file: Optional path to config file
        cli_overrides: Optional dictionary of CLI flag values
    
    Returns:
        Complete LLMConfig object
    
    Examples:
        >>> config = get_llm_config()
        >>> config.engine
        'openai'
        
        >>> cli = {"engine": "ollama", "model": "llama3.2:3b"}
        >>> config = get_llm_config(cli_overrides=cli)
        >>> config.model
        'llama3.2:3b'
    """
    # Load from config file
    file_config = load_config_file(config_file)
    
    # Load from environment
    env_config = load_from_env()
    
    # Merge: defaults < file < env < CLI
    merged = merge_configs(
        file_config,
        env_config,
        cli_overrides or {}
    )
    
    # Create LLMConfig object
    return LLMConfig(**merged)


def validate_api_key_security(config: LLMConfig) -> None:
    """Validate that API keys are not exposed in insecure ways.
    
    Raises:
        ValueError: If API key security requirements are violated
    """
    # API keys should ONLY come from environment variables, never from:
    # - Command-line flags (visible in process list)
    # - Config files (might be committed to git)
    if config.api_key:
        # Verify it came from environment
        if config.api_key != os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "API keys must be set via OPENAI_API_KEY environment variable, "
                "not via config file or CLI flags (security risk)"
            )


def create_example_config() -> str:
    """Generate example configuration file content.
    
    Returns:
        TOML configuration file content as string
    """
    return """\
# Mnemofy LLM Configuration
# Save this file as: ~/.config/mnemofy/config.toml

[llm]
# LLM engine: "openai", "ollama", or "openai_compat"
engine = "openai"

# Model name (optional, uses engine default if not specified)
# OpenAI: "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"
# Ollama: "llama3.2:3b", "mistral:latest", "codellama:latest"
model = "gpt-4o-mini"

# Custom API endpoint (optional)
# base_url = "https://api.openai.com/v1"
# base_url = "http://localhost:11434"  # Ollama default

# Request timeout in seconds
timeout = 30

# Maximum retry attempts on failure
max_retries = 2

# Enable LLM features by default
enabled = false

# Fall back to heuristic mode if LLM fails
fallback_to_heuristic = true

# High-signal segment extraction settings
context_words = 50  # Words before/after decision markers
max_segments = 10   # Maximum segments to extract

# SECURITY NOTE:
# API keys MUST be set via environment variables, not in this file:
#   export OPENAI_API_KEY="sk-..."
#   export OLLAMA_HOST="http://localhost:11434"
"""
