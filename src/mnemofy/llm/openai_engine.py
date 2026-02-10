"""OpenAI-compatible API LLM engine."""

import json
import os
from typing import Dict, List, Any, Optional
import httpx

from mnemofy.llm.base import BaseLLMEngine, LLMError
from mnemofy.classifier import ClassificationResult, MeetingType, GroundedItem, TranscriptReference


class OpenAIEngine(BaseLLMEngine):
    """LLM engine for OpenAI-compatible APIs.
    
    Supports OpenAI API and any compatible endpoint (e.g., Azure OpenAI, local vLLM).
    """
    
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 2
    ):
        """Initialize OpenAI engine.
        
        Args:
            model: Model name (default: gpt-4o-mini)
            base_url: API base URL (default: OpenAI API)
            api_key: API key (from OPENAI_API_KEY env var if not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts on failure
        """
        self.model = model or self.DEFAULT_MODEL
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create HTTP client with retry logic
        self.client = httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        )
    
    def health_check(self) -> bool:
        """Check if OpenAI API is reachable."""
        if not self.api_key:
            return False
        
        try:
            response = self.client.get(f"{self.base_url}/models", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def classify_meeting_type(
        self,
        transcript_text: str,
        high_signal_segments: Optional[List[str]] = None
    ) -> ClassificationResult:
        """Classify meeting type using OpenAI."""
        # Build context from transcript window + high-signal segments
        context_parts = []
        
        # Use first 10-15 minutes of transcript
        words = transcript_text.split()
        window_size = min(3000, len(words))  # ~10-15 min at 3-5 words/sec
        context_parts.append(" ".join(words[:window_size]))
        
        # Add high-signal segments
        if high_signal_segments:
            context_parts.append("\n\n[Key Discussion Points]")
            context_parts.extend(high_signal_segments[:5])
        
        context = "\n".join(context_parts)
        
        # Classification prompt
        prompt = f"""Analyze this meeting transcript and classify its type.

Meeting Types:
- status: Daily standup, progress update, status check
- planning: Sprint planning, roadmap, project planning
- design: Technical design, architecture discussion
- demo: Feature demonstration, product showcase
- talk: Presentation, lecture, educational session
- incident: Incident response, troubleshooting, RCA
- discovery: User research, requirements gathering
- oneonone: 1:1 check-in, career discussion, feedback
- brainstorm: Ideation session, creative thinking

Transcript:
{context}

Respond in JSON format:
{{
  "type": "one of the meeting types above",
  "confidence": 0.0-1.0,
  "evidence": ["phrase1", "phrase2", "phrase3"],
  "notes_focus": ["what to emphasize in notes"]
}}"""

        try:
            response = self._call_api([
                {"role": "system", "content": "You are a meeting analysis expert."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse JSON response
            result_data = json.loads(response)
            detected_type = MeetingType(result_data["type"])
            
            return ClassificationResult(
                detected_type=detected_type,
                confidence=result_data["confidence"],
                evidence=result_data.get("evidence", []),
                secondary_types=[],  # LLM doesn't provide alternatives
                engine="llm"
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise LLMError(f"Invalid LLM response: {e}")
    
    def generate_notes(
        self,
        transcript_segments: List[Dict[str, Any]],
        meeting_type: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, List[GroundedItem]]:
        """Generate structured notes using OpenAI.
        
        Enforces grounding: all extracted items must have timestamp references.
        """
        # Build transcript with timestamps
        formatted_segments = []
        for seg in transcript_segments:
            start = int(seg['start'])
            speaker = seg.get('speaker', 'Speaker')
            text = seg['text']
            formatted_segments.append(f"[{start}s] {speaker}: {text}")
        
        transcript = "\n".join(formatted_segments[:100])  # Limit to first 100 segments
        
        # Notes extraction prompt
        focus_str = ", ".join(focus_areas) if focus_areas else "decisions, action items, key mentions"
        prompt = f"""Extract structured information from this {meeting_type} meeting transcript.

CRITICAL REQUIREMENTS:
1. Use ONLY information from the transcript
2. Include timestamp references for ALL extracted items
3. If you cannot find evidence in the transcript, mark item as "unclear" with a reason
4. Format: [timestamp]s for each item

Extract:
- {focus_str}

Transcript:
{transcript}

Respond in JSON format:
{{
  "decisions": [
    {{"text": "decision text", "timestamp": 123, "status": "confirmed|unclear", "reason": "if unclear"}}
  ],
  "actions": [
    {{"text": "action text", "timestamp": 456, "owner": "person", "status": "confirmed|unclear"}}
  ],
  "mentions": [
    {{"text": "key mention", "timestamp": 789, "type": "name|url|date|number"}}
  ]
}}"""

        try:
            response = self._call_api([
                {"role": "system", "content": "You extract grounded information from meeting transcripts."},
                {"role": "user", "content": prompt}
            ])
            
            # Parse and convert to GroundedItems
            data = json.loads(response)
            result = {}
            
            for category in ["decisions", "actions", "mentions"]:
                items = []
                for item_data in data.get(category, []):
                    # Create transcript reference
                    timestamp = item_data.get("timestamp", 0)
                    ref = TranscriptReference(
                        reference_id=f"llm-{timestamp}",
                        start_time=float(timestamp),
                        end_time=float(timestamp) + 5.0,
                        speaker=item_data.get("owner"),
                        text_snippet=item_data.get("text", "")[:100]
                    )
                    
                    # Create grounded item
                    item = GroundedItem(
                        text=item_data["text"],
                        status=item_data.get("status", "confirmed"),
                        reason=item_data.get("reason"),
                        references=[ref],
                        item_type=category[:-1] if category.endswith("s") else category,  # Remove plural
                        metadata={"owner": item_data.get("owner"), "mention_type": item_data.get("type")}
                    )
                    items.append(item)
                
                result[category] = items
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            raise LLMError(f"Invalid LLM response: {e}")
    
    def get_model_name(self) -> str:
        """Get model name."""
        return self.model
    
    def _call_api(self, messages: List[Dict[str, str]], temperature: float = 0.0) -> str:
        """Call OpenAI API with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
            except httpx.TimeoutException:
                if attempt == self.max_retries:
                    raise LLMError("LLM request timeout")
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries:
                    raise LLMError(f"LLM API error: {e.response.status_code}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise LLMError(f"LLM request failed: {e}")
        
        raise LLMError("Max retries exceeded")
    
    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
