"""Tests for LLM engine implementations."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from mnemofy.classifier import ClassificationResult, MeetingType, GroundedItem
from mnemofy.llm import get_llm_engine
from mnemofy.llm.base import LLMError
from mnemofy.llm.openai_engine import OpenAIEngine
from mnemofy.llm.ollama_engine import OllamaEngine


class TestLLMFactory:
    """Test get_llm_engine factory function."""
    
    @patch.object(OpenAIEngine, 'health_check', return_value=True)
    def test_create_openai_engine(self, mock_health):
        """Should create OpenAI engine when healthy."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            engine = get_llm_engine("openai", model="gpt-4o-mini")
            assert engine is not None
            assert isinstance(engine, OpenAIEngine)
            assert engine.get_model_name() == "gpt-4o-mini"
    
    @patch.object(OllamaEngine, 'health_check', return_value=True)
    def test_create_ollama_engine(self, mock_health):
        """Should create Ollama engine when healthy."""
        engine = get_llm_engine("ollama", model="llama3.2:3b")
        assert engine is not None
        assert isinstance(engine, OllamaEngine)
        assert engine.get_model_name() == "llama3.2:3b"
    
    @patch.object(OpenAIEngine, 'health_check', return_value=False)
    def test_unhealthy_engine_returns_none(self, mock_health):
        """Should return None if engine fails health check."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            engine = get_llm_engine("openai")
            assert engine is None
    
    def test_invalid_engine_type_returns_none(self):
        """Should return None for unknown engine types."""
        engine = get_llm_engine("invalid_engine")
        assert engine is None


class TestOpenAIEngine:
    """Test OpenAI-compatible engine."""
    
    def test_initialization_with_env_key(self):
        """Should use API key from environment."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            engine = OpenAIEngine()
            assert engine.api_key == 'env-key'
            assert engine.model == OpenAIEngine.DEFAULT_MODEL
    
    def test_initialization_with_explicit_key(self):
        """Should use explicit API key over environment."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            engine = OpenAIEngine(api_key='explicit-key')
            assert engine.api_key == 'explicit-key'
    
    def test_health_check_success(self):
        """Should return True when API is reachable."""
        engine = OpenAIEngine(api_key='test-key')
        
        with patch.object(engine.client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            assert engine.health_check() is True
    
    def test_health_check_no_api_key(self):
        """Should return False when no API key provided."""
        engine = OpenAIEngine(api_key='')
        assert engine.health_check() is False
    
    def test_classify_meeting_type_success(self):
        """Should classify meeting type using LLM."""
        engine = OpenAIEngine(api_key='test-key')
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"type": "planning", "confidence": 0.92, "evidence": ["sprint planning", "backlog"], "notes_focus": ["milestones"]}'
                }
            }]
        }
        
        with patch.object(engine.client, 'post', return_value=mock_response):
            result = engine.classify_meeting_type("Let's do sprint planning and review the backlog")
            
            assert isinstance(result, ClassificationResult)
            assert result.detected_type == MeetingType.PLANNING
            assert result.confidence == 0.92
            assert "sprint planning" in result.evidence
            assert result.engine == "llm"
    
    def test_classify_with_high_signal_segments(self):
        """Should use high-signal segments for classification."""
        engine = OpenAIEngine(api_key='test-key')
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"type": "incident", "confidence": 0.95, "evidence": ["outage", "RCA"]}'
                }
            }]
        }
        
        high_signal = ["we have an outage", "need to do RCA"]
        
        with patch.object(engine.client, 'post', return_value=mock_response) as mock_post:
            engine.classify_meeting_type("transcript text", high_signal_segments=high_signal)
            
            # Verify high-signal segments included in prompt
            call_args = mock_post.call_args
            prompt = call_args[1]['json']['messages'][1]['content']
            assert "[Key Discussion Points]" in prompt
            assert "we have an outage" in prompt
    
    def test_generate_notes_with_grounding(self):
        """Should extract notes with timestamp grounding."""
        engine = OpenAIEngine(api_key='test-key')
        
        segments = [
            {"start": 10.0, "end": 15.0, "text": "We decided to use PostgreSQL", "speaker": "Alice"},
            {"start": 20.0, "end": 25.0, "text": "Bob will implement it", "speaker": "Bob"},
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '''{
                        "decisions": [{"text": "Use PostgreSQL", "timestamp": 10, "status": "confirmed"}],
                        "actions": [{"text": "Implement PostgreSQL", "timestamp": 20, "owner": "Bob", "status": "confirmed"}],
                        "mentions": []
                    }'''
                }
            }]
        }
        
        with patch.object(engine.client, 'post', return_value=mock_response):
            result = engine.generate_notes(segments, "design")
            
            assert "decisions" in result
            assert "actions" in result
            assert len(result["decisions"]) == 1
            assert len(result["actions"]) == 1
            
            # Check grounding
            decision = result["decisions"][0]
            assert isinstance(decision, GroundedItem)
            assert decision.text == "Use PostgreSQL"
            assert decision.status == "confirmed"
            assert len(decision.references) > 0
            assert decision.references[0].start_time == 10.0
    
    def test_api_call_retry_on_timeout(self):
        """Should retry on timeout errors."""
        engine = OpenAIEngine(api_key='test-key', max_retries=2)
        
        with patch.object(engine.client, 'post') as mock_post:
            # First two calls timeout, third succeeds
            mock_post.side_effect = [
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                MagicMock(status_code=200, json=lambda: {"choices": [{"message": {"content": "test"}}]})
            ]
            
            messages = [{"role": "user", "content": "test"}]
            result = engine._call_api(messages)
            assert result == "test"
            assert mock_post.call_count == 3
    
    def test_api_call_max_retries_exceeded(self):
        """Should raise LLMError after max retries."""
        engine = OpenAIEngine(api_key='test-key', max_retries=1)
        
        with patch.object(engine.client, 'post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("timeout")
            
            with pytest.raises(LLMError, match="timeout"):
                engine._call_api([{"role": "user", "content": "test"}])


class TestOllamaEngine:
    """Test Ollama local engine."""
    
    def test_initialization_defaults(self):
        """Should use default Ollama settings."""
        engine = OllamaEngine()
        assert engine.model == OllamaEngine.DEFAULT_MODEL
        assert engine.base_url == OllamaEngine.DEFAULT_BASE_URL
    
    def test_health_check_model_available(self):
        """Should return True when Ollama is running and model is pulled."""
        engine = OllamaEngine(model="llama3.2:3b")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "mistral:latest"}
            ]
        }
        
        with patch.object(engine.client, 'get', return_value=mock_response):
            assert engine.health_check() is True
    
    def test_health_check_model_not_pulled(self):
        """Should return False when model not available."""
        engine = OllamaEngine(model="missing-model:latest")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2:3b"}]
        }
        
        with patch.object(engine.client, 'get', return_value=mock_response):
            assert engine.health_check() is False
    
    def test_classify_meeting_type_with_json_mode(self):
        """Should use Ollama's JSON mode for classification."""
        engine = OllamaEngine(model="llama3.2:3b")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '{"type": "status", "confidence": 0.88, "evidence": ["standup", "updates"]}'
        }
        
        with patch.object(engine.client, 'post', return_value=mock_response) as mock_post:
            result = engine.classify_meeting_type("Daily standup with status updates")
            
            # Verify JSON mode enabled
            call_args = mock_post.call_args
            assert call_args[1]['json']['format'] == 'json'
            
            assert result.detected_type == MeetingType.STATUS
            assert result.confidence == 0.88
    
    def test_model_not_found_error(self):
        """Should raise helpful error when model not pulled."""
        engine = OllamaEngine(model="missing:latest", max_retries=0)
        
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(engine.client, 'post') as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Not found",
                request=Mock(),
                response=mock_response
            )
            
            with pytest.raises(LLMError, match="Model 'missing:latest' not found"):
                engine._call_api("test prompt")


class TestLLMGrounding:
    """Test grounding validation for LLM-extracted content."""
    
    def test_all_items_have_references(self):
        """All extracted items must have transcript references."""
        engine = OpenAIEngine(api_key='test-key')
        
        segments = [
            {"start": 5.0, "end": 10.0, "text": "We need to fix the bug", "speaker": "Alice"},
        ]
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"decisions": [], "actions": [{"text": "Fix bug", "timestamp": 5}], "mentions": []}'
                }
            }]
        }
        
        with patch.object(engine.client, 'post', return_value=mock_response):
            result = engine.generate_notes(segments, "incident")
            
            # Every action item must have a reference
            for action in result["actions"]:
                assert len(action.references) > 0
                assert action.references[0].start_time >= 0
                assert action.references[0].text_snippet is not None
