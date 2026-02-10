"""Ollama local LLM engine."""

import json
from typing import Dict, List, Any, Optional
import httpx

from mnemofy.llm.base import BaseLLMEngine, LLMError
from mnemofy.classifier import ClassificationResult, MeetingType, GroundedItem, TranscriptReference


class OllamaEngine(BaseLLMEngine):
    """LLM engine for Ollama local models.
    
    Ollama provides local LLM inference without requiring API keys.
    """
    
    DEFAULT_MODEL = "llama3.2:3b"
    DEFAULT_BASE_URL = "http://localhost:11434"
    
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 2
    ):
        """Initialize Ollama engine.
        
        Args:
            model: Model name (default: llama3.2:3b)
            base_url: Ollama API URL (default: http://localhost:11434)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.model = model or self.DEFAULT_MODEL
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.client = httpx.Client(timeout=timeout)
    
    def health_check(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            # Check if Ollama is running
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if model is pulled
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            return self.model in model_names
            
        except Exception:
            return False
    
    def classify_meeting_type(
        self,
        transcript_text: str,
        high_signal_segments: Optional[List[str]] = None
    ) -> ClassificationResult:
        """Classify meeting type using Ollama."""
        # Build context
        context_parts = []
        words = transcript_text.split()
        window_size = min(2000, len(words))  # Shorter window for local models
        context_parts.append(" ".join(words[:window_size]))
        
        if high_signal_segments:
            context_parts.append("\n\n[Key Points]")
            context_parts.extend(high_signal_segments[:3])
        
        context = "\n".join(context_parts)
        
        prompt = f"""Classify this meeting transcript. Choose ONE type:
status, planning, design, demo, talk, incident, discovery, oneonone, brainstorm

Transcript:
{context}

JSON response (exactly this format):
{{"type": "classified_type", "confidence": 0.85, "evidence": ["reason1", "reason2"]}}"""

        try:
            response = self._call_api(prompt, json_mode=True)
            result_data = json.loads(response)
            detected_type = MeetingType(result_data["type"])
            
            return ClassificationResult(
                detected_type=detected_type,
                confidence=min(result_data.get("confidence", 0.7), 1.0),
                evidence=result_data.get("evidence", []),
                secondary_types=[],
                engine="llm"
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise LLMError(f"Invalid Ollama response: {e}")
    
    def generate_notes(
        self,
        transcript_segments: List[Dict[str, Any]],
        meeting_type: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, List[GroundedItem]]:
        """Generate structured notes using Ollama."""
        # Format transcript with timestamps
        formatted = []
        for seg in transcript_segments[:80]:  # Shorter for local models
            start = int(seg['start'])
            text = seg['text']
            formatted.append(f"[{start}s] {text}")
        
        transcript = "\n".join(formatted)
        
        prompt = f"""Extract from this {meeting_type} meeting:
- decisions (with timestamp)
- actions (with timestamp)
- key mentions (with timestamp)

Transcript:
{transcript}

JSON format only:
{{"decisions": [{{"text": "...", "timestamp": 10}}], "actions": [{{"text": "...", "timestamp": 20}}], "mentions": [{{"text": "...", "timestamp": 30}}]}}"""

        try:
            response = self._call_api(prompt, json_mode=True)
            data = json.loads(response)
            
            # Convert to GroundedItems (same as OpenAI)
            result = {}
            for category in ["decisions", "actions", "mentions"]:
                items = []
                for item_data in data.get(category, []):
                    timestamp = item_data.get("timestamp", 0)
                    ref = TranscriptReference(
                        reference_id=f"ollama-{timestamp}",
                        start_time=float(timestamp),
                        end_time=float(timestamp) + 5.0,
                        speaker=None,
                        text_snippet=item_data.get("text", "")[:100]
                    )
                    
                    item = GroundedItem(
                        text=item_data["text"],
                        status="confirmed",
                        reason=None,
                        references=[ref],
                        item_type=category[:-1],
                        metadata={}
                    )
                    items.append(item)
                
                result[category] = items
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            raise LLMError(f"Invalid Ollama response: {e}")
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self.model
    
    def _call_api(self, prompt: str, json_mode: bool = False) -> str:
        """Call Ollama API with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                }
                
                if json_mode:
                    payload["format"] = "json"
                
                response = self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
                
            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    raise LLMError("Ollama request timeout")
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries:
                    # Check if model not pulled
                    if e.response.status_code == 404:
                        raise LLMError(f"Model '{self.model}' not found. Run: ollama pull {self.model}")
                    raise LLMError(f"Ollama API error: {e.response.status_code}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise LLMError(f"Ollama request failed: {e}")
        
        raise LLMError("Max retries exceeded")
    
    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
