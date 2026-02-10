"""Tests for LLM configuration management."""

import os
import tempfile
from pathlib import Path
import pytest

from mnemofy.llm.config import (
    LLMConfig,
    load_config_file,
    load_from_env,
    merge_configs,
    get_llm_config,
    validate_api_key_security,
    create_example_config,
)


class TestConfigFileLoading:
    """Test TOML configuration file loading."""
    
    def test_load_valid_config_file(self):
        """Should load valid TOML configuration."""
        config_content = """
[llm]
engine = "ollama"
model = "llama3.2:3b"
timeout = 60
enabled = true
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            config = load_config_file(config_path)
            assert config["engine"] == "ollama"
            assert config["model"] == "llama3.2:3b"
            assert config["timeout"] == 60
            assert config["enabled"] is True
        finally:
            config_path.unlink()
    
    def test_load_nonexistent_file(self):
        """Should return empty dict when file doesn't exist."""
        config = load_config_file(Path("/nonexistent/path/config.toml"))
        assert config == {}
    
    def test_load_invalid_toml(self):
        """Should handle invalid TOML gracefully."""
        config_content = "this is not valid TOML [["
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            config = load_config_file(config_path)
            assert config == {}  # Should fail silently
        finally:
            config_path.unlink()
    
    def test_default_config_locations(self):
        """Should check standard config locations."""
        # This test just verifies the function doesn't crash
        # when searching for default config files
        config = load_config_file()
        assert isinstance(config, dict)


class TestEnvironmentLoading:
    """Test environment variable configuration."""
    
    def test_load_engine_from_env(self):
        """Should load engine from MNEMOFY_LLM_ENGINE."""
        with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_ENGINE': 'ollama'}):
            config = load_from_env()
            assert config["engine"] == "ollama"
    
    def test_load_model_from_env(self):
        """Should load model from MNEMOFY_LLM_MODEL."""
        with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_MODEL': 'gpt-4o'}):
            config = load_from_env()
            assert config["model"] == "gpt-4o"
    
    def test_load_api_key_from_env(self):
        """Should load API key from OPENAI_API_KEY."""
        with pytest.mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test123'}):
            config = load_from_env()
            assert config["api_key"] == "sk-test123"
    
    def test_load_base_url_from_env(self):
        """Should load base URL from MNEMOFY_LLM_BASE_URL."""
        with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_BASE_URL': 'http://custom:8000'}):
            config = load_from_env()
            assert config["base_url"] == "http://custom:8000"
    
    def test_load_ollama_host_from_env(self):
        """Should use OLLAMA_HOST for base_url if set."""
        with pytest.mock.patch.dict(os.environ, {'OLLAMA_HOST': 'http://ollama-server:11434'}):
            config = load_from_env()
            assert config["base_url"] == "http://ollama-server:11434"
    
    def test_load_timeout_from_env(self):
        """Should parse timeout as integer."""
        with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_TIMEOUT': '45'}):
            config = load_from_env()
            assert config["timeout"] == 45
    
    def test_load_enabled_flag_from_env(self):
        """Should parse enabled flag as boolean."""
        test_cases = [
            ('true', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('0', False),
        ]
        
        for value, expected in test_cases:
            with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_ENABLED': value}, clear=True):
                config = load_from_env()
                assert config.get("enabled") == expected
    
    def test_invalid_timeout_ignored(self):
        """Should ignore invalid timeout values."""
        with pytest.mock.patch.dict(os.environ, {'MNEMOFY_LLM_TIMEOUT': 'invalid'}):
            config = load_from_env()
            assert "timeout" not in config


class TestConfigMerging:
    """Test configuration merging logic."""
    
    def test_merge_empty_configs(self):
        """Should handle empty config dicts."""
        result = merge_configs({}, {})
        assert result == {}
    
    def test_merge_overwrites_earlier_values(self):
        """Later configs should override earlier ones."""
        config1 = {"engine": "openai", "model": "gpt-3.5-turbo"}
        config2 = {"model": "gpt-4o"}
        
        result = merge_configs(config1, config2)
        assert result["engine"] == "openai"  # From config1
        assert result["model"] == "gpt-4o"   # Overridden by config2
    
    def test_merge_ignores_none_values(self):
        """Should not override with None values."""
        config1 = {"engine": "openai", "model": "gpt-4o"}
        config2 = {"model": None, "timeout": 60}
        
        result = merge_configs(config1, config2)
        assert result["model"] == "gpt-4o"  # Not overridden by None
        assert result["timeout"] == 60
    
    def test_merge_multiple_configs(self):
        """Should support merging multiple configs."""
        defaults = {"engine": "openai", "timeout": 30}
        file_config = {"model": "gpt-4o-mini"}
        env_config = {"timeout": 60}
        cli_config = {"engine": "ollama"}
        
        result = merge_configs(defaults, file_config, env_config, cli_config)
        assert result["engine"] == "ollama"      # CLI wins
        assert result["model"] == "gpt-4o-mini"  # From file
        assert result["timeout"] == 60           # Env overrides defaults


class TestFullConfigResolution:
    """Test complete configuration resolution."""
    
    def test_get_config_with_defaults(self):
        """Should return default config when no overrides."""
        with pytest.mock.patch.dict(os.environ, {}, clear=True):
            config = get_llm_config()
            
            assert isinstance(config, LLMConfig)
            assert config.engine == "openai"
            assert config.timeout == 30
            assert config.fallback_to_heuristic is True
    
    def test_get_config_with_env_overrides(self):
        """Should apply environment variable overrides."""
        env_vars = {
            'MNEMOFY_LLM_ENGINE': 'ollama',
            'MNEMOFY_LLM_MODEL': 'llama3.2:3b',
            'MNEMOFY_LLM_TIMEOUT': '45',
        }
        
        with pytest.mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_llm_config()
            
            assert config.engine == "ollama"
            assert config.model == "llama3.2:3b"
            assert config.timeout == 45
    
    def test_get_config_with_cli_overrides(self):
        """CLI overrides should have highest priority."""
        env_vars = {'MNEMOFY_LLM_ENGINE': 'ollama'}
        cli_overrides = {
            'engine': 'openai',
            'model': 'gpt-4o',
        }
        
        with pytest.mock.patch.dict(os.environ, env_vars, clear=True):
            config = get_llm_config(cli_overrides=cli_overrides)
            
            assert config.engine == "openai"  # CLI beats env
            assert config.model == "gpt-4o"
    
    def test_get_config_with_file(self):
        """Should load from specified config file."""
        config_content = """
[llm]
engine = "ollama"
model = "mistral:latest"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            with pytest.mock.patch.dict(os.environ, {}, clear=True):
                config = get_llm_config(config_file=config_path)
                
                assert config.engine == "ollama"
                assert config.model == "mistral:latest"
        finally:
            config_path.unlink()
    
    def test_priority_order(self):
        """Test complete priority chain: defaults < file < env < CLI."""
        # Create config file
        config_content = """
[llm]
engine = "ollama"
model = "file-model"
timeout = 50
context_words = 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        try:
            env_vars = {
                'MNEMOFY_LLM_MODEL': 'env-model',
                'MNEMOFY_LLM_TIMEOUT': '70',
            }
            cli_overrides = {
                'model': 'cli-model',
            }
            
            with pytest.mock.patch.dict(os.environ, env_vars, clear=True):
                config = get_llm_config(
                    config_file=config_path,
                    cli_overrides=cli_overrides
                )
                
                # Default values
                assert config.fallback_to_heuristic is True  # Default
                
                # File values (not overridden)
                assert config.engine == "ollama"  # From file, not overridden
                assert config.context_words == 100  # From file
                
                # Env overrides file
                assert config.timeout == 70  # Env beats file
                
                # CLI overrides everything
                assert config.model == "cli-model"  # CLI beats env and file
        finally:
            config_path.unlink()


class TestAPIKeySecurity:
    """Test API key security validation."""
    
    def test_api_key_from_env_is_valid(self):
        """Should allow API key from environment variable."""
        with pytest.mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-valid'}):
            config = LLMConfig(api_key=os.getenv('OPENAI_API_KEY'))
            # Should not raise
            validate_api_key_security(config)
    
    def test_api_key_not_from_env_raises_error(self):
        """Should reject API keys not from environment."""
        with pytest.mock.patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(api_key='sk-insecure')
            
            with pytest.raises(ValueError, match="must be set via OPENAI_API_KEY"):
                validate_api_key_security(config)
    
    def test_no_api_key_is_valid(self):
        """Should allow configs without API keys."""
        config = LLMConfig(api_key=None)
        # Should not raise
        validate_api_key_security(config)


class TestExampleConfig:
    """Test example config generation."""
    
    def test_create_example_config_is_valid_toml(self):
        """Generated example should be parsable TOML."""
        example = create_example_config()
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        # Should parse without errors
        data = tomllib.loads(example)
        assert "llm" in data
        assert "engine" in data["llm"]
    
    def test_example_config_has_security_notice(self):
        """Example should warn about API key security."""
        example = create_example_config()
        assert "SECURITY NOTE" in example or "SECURITY" in example
        assert "OPENAI_API_KEY" in example
