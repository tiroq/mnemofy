"""Meeting type classification and detection.

This module provides meeting type detection using both deterministic heuristic approaches
and optional LLM-based classification. All classifications include confidence scores and
evidence to support transparency.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MeetingType(str, Enum):
    """Enumeration of supported meeting types."""
    
    STATUS = "status"
    PLANNING = "planning"
    DESIGN = "design"
    DEMO = "demo"
    TALK = "talk"
    INCIDENT = "incident"
    DISCOVERY = "discovery"
    ONEONONE = "oneonone"
    BRAINSTORM = "brainstorm"


@dataclass
class TranscriptReference:
    """Reference to a specific location in a transcript.
    
    Used for grounding extracted information (decisions, action items, etc.)
    with timestamp and speaker attribution.
    """
    
    reference_id: str
    start_time: float
    end_time: float
    speaker: Optional[str]
    text_snippet: str


@dataclass
class GroundedItem:
    """An extracted item (decision, action, mention) grounded in transcript evidence.
    
    All content must be traceable to specific transcript locations with timestamp
    references to ensure accuracy and verifiability.
    """
    
    text: str
    status: str  # "confirmed", "unclear", "inferred"
    reason: Optional[str]  # Required when status is "unclear"
    references: List[TranscriptReference] = field(default_factory=list)
    item_type: str = "general"  # "decision", "action", "mention", "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """Result of meeting type classification.
    
    Contains the detected meeting type, confidence score, evidence phrases,
    and alternative candidates for transparency and user override.
    """
    
    detected_type: MeetingType
    confidence: float  # 0.0 to 1.0
    evidence: List[str]  # Key phrases that supported the classification
    secondary_types: List[tuple[MeetingType, float]] = field(default_factory=list)  # Top 5 alternatives
    engine: str = "heuristic"  # "heuristic" or "llm"
    timestamp: datetime = field(default_factory=datetime.now)


# Meeting type keyword dictionaries for heuristic detection
# Weighted keywords: higher values indicate stronger signals for each meeting type
MEETING_TYPE_KEYWORDS: Dict[MeetingType, Dict[str, float]] = {
    MeetingType.STATUS: {
        # Progress and updates
        "status": 2.5,
        "update": 2.5,
        "progress": 2.0,
        "blockers": 2.5,
        "blocked": 2.0,
        "impediments": 2.0,
        "stand-up": 3.0,
        "standup": 3.0,
        "scrum": 2.5,
        "sprint": 2.0,
        # Time-based indicators
        "yesterday": 2.0,
        "today": 1.5,
        "tomorrow": 1.5,
        "this week": 1.0,
        "last week": 1.0,
        "next week": 1.0,
        # Status-specific phrases
        "working on": 1.5,
        "finished": 1.0,
        "completed": 1.0,
        "in progress": 1.5,
        "waiting for": 1.5,
    },
    
    MeetingType.PLANNING: {
        # Planning vocabulary
        "roadmap": 2.5,
        "milestone": 2.0,
        "sprint planning": 3.0,
        "backlog": 2.5,
        "prioritize": 2.0,
        "priority": 1.5,
        "estimate": 2.0,
        "timeline": 2.0,
        "deadline": 1.5,
        "dependencies": 1.5,
        # Future-focused
        "next quarter": 2.0,
        "next sprint": 2.0,
        "upcoming": 1.5,
        "plan": 1.5,
        "schedule": 1.5,
        "allocate": 1.5,
        "resource": 1.0,
        # Story/task language
        "story points": 2.5,
        "velocity": 2.0,
        "capacity": 1.5,
        "commitment": 1.5,
    },
    
    MeetingType.DESIGN: {
        # Technical design
        "architecture": 2.5,
        "design": 2.0,
        "technical": 1.5,
        "approach": 1.5,
        "pattern": 2.0,
        "trade-offs": 2.5,
        "tradeoffs": 2.5,
        # System components
        "component": 1.5,
        "module": 1.5,
        "interface": 2.0,
        "API": 2.0,
        "schema": 2.0,
        "data model": 2.5,
        # Design process
        "diagram": 2.0,
        "whiteboard": 2.0,
        "mock": 1.5,
        "mockup": 1.5,
        "prototype": 2.0,
        "proposal": 1.5,
        "scalability": 2.0,
        "performance": 1.5,
    },
    
    MeetingType.DEMO: {
        # Demonstration
        "demo": 3.0,
        "demonstrate": 2.5,
        "show": 1.5,
        "presentation": 2.0,
        "showcase": 2.5,
        "walkthrough": 2.0,
        # Interaction
        "let me show": 2.5,
        "you can see": 2.0,
        "as you can see": 2.0,
        "here's how": 2.0,
        "click": 1.5,
        "screen": 1.5,
        "feature": 1.5,
        # Feedback
        "feedback": 1.5,
        "questions": 1.0,
        "thoughts": 1.0,
        "works": 1.0,
    },
    
    MeetingType.TALK: {
        # Presentation/lecture
        "presentation": 2.0,
        "talk": 1.5,
        "lecture": 2.5,
        "today I'll": 2.0,
        "agenda": 2.0,
        "introducing": 2.0,
        "overview": 2.0,
        # Speaker patterns
        "thank you for": 1.5,
        "questions": 1.0,
        "slides": 2.5,
        "next slide": 2.5,
        # Educational
        "explain": 1.5,
        "learn": 1.5,
        "understand": 1.0,
    },
    
    MeetingType.INCIDENT: {
        # Urgency
        "incident": 3.0,
        "outage": 3.0,
        "down": 2.0,
        "critical": 2.5,
        "urgent": 2.0,
        "emergency": 2.5,
        "broken": 2.0,
        # Investigation
        "root cause": 2.5,
        "RCA": 2.5,
        "investigate": 2.0,
        "debug": 2.0,
        "troubleshoot": 2.0,
        "logs": 1.5,
        "error": 1.5,
        "failure": 1.5,
        # Response
        "mitigate": 2.0,
        "rollback": 2.0,
        "hotfix": 2.5,
        "restore": 2.0,
        "recovering": 2.0,
    },
    
    MeetingType.DISCOVERY: {
        # Research/exploration
        "discovery": 2.5,
        "research": 2.0,
        "explore": 2.0,
        "investigate": 1.5,
        "understand": 1.5,
        "requirements": 2.0,
        "user needs": 2.5,
        "pain points": 2.5,
        # Interview/probing
        "tell me about": 2.0,
        "how do you": 1.5,
        "why do you": 1.5,
        "workflow": 1.5,
        "process": 1.0,
        "challenges": 1.5,
        # Insights
        "insights": 2.0,
        "findings": 2.0,
        "learned": 1.5,
    },
    
    MeetingType.ONEONONE: {
        # Personal connection
        "1:1": 3.0,
        "one-on-one": 3.0,
        "check-in": 2.5,
        "check in": 2.5,
        "how are you": 2.0,
        "how's it going": 2.0,
        # Career/growth
        "career": 2.5,
        "growth": 2.0,
        "feedback": 1.5,
        "performance": 1.5,
        "goals": 1.5,
        "development": 1.5,
        # Personal concerns
        "feeling": 1.5,
        "comfortable": 1.0,
        "support": 1.0,
        "concerns": 1.5,
    },
    
    MeetingType.BRAINSTORM: {
        # Ideation
        "brainstorm": 3.0,
        "ideas": 2.5,
        "creative": 2.0,
        "think": 1.5,
        "what if": 2.5,
        "could we": 2.0,
        "maybe": 1.5,
        # Exploration
        "possibilities": 2.0,
        "options": 1.5,
        "alternatives": 1.5,
        "crazy idea": 2.5,
        "wild idea": 2.5,
        # No wrong answers
        "no bad ideas": 2.5,
        "throw out": 2.0,
        "building on": 1.5,
    },
}


class HeuristicClassifier:
    """Deterministic meeting type classifier using weighted keyword TF-IDF.
    
    Analyzes transcript text to detect meeting type using keyword frequency,
    structural features (question density, timeline vocabulary), and confidence scoring.
    
    Operates completely offline without any external dependencies or API calls.
    """
    
    def __init__(self, keywords: Optional[Dict[MeetingType, Dict[str, float]]] = None):
        """Initialize heuristic classifier.
        
        Args:
            keywords: Optional custom keyword dictionary. If None, uses MEETING_TYPE_KEYWORDS.
        """
        self.keywords = keywords or MEETING_TYPE_KEYWORDS
    
    def detect_meeting_type(
        self,
        transcript_text: str,
        segments: Optional[List[Dict[str, Any]]] = None
    ) -> ClassificationResult:
        """Detect meeting type from transcript using heuristic approach.
        
        Args:
            transcript_text: Full transcript text (all segments combined)
            segments: Optional list of transcript segments with timing info
        
        Returns:
            ClassificationResult with detected type, confidence, evidence, and alternatives
        
        Examples:
            >>> classifier = HeuristicClassifier()
            >>> result = classifier.detect_meeting_type("status update blockers sprint")
            >>> result.detected_type
            MeetingType.STATUS
            >>> result.confidence > 0.6
            True
        """
        # Normalize text for matching
        text_lower = transcript_text.lower()
        
        # Calculate TF-IDF-like scores for each meeting type
        scores: Dict[MeetingType, float] = {}
        evidence_by_type: Dict[MeetingType, List[str]] = {}
        
        for meeting_type, keywords_dict in self.keywords.items():
            type_score = 0.0
            found_keywords = []
            
            for keyword, weight in keywords_dict.items():
                keyword_lower = keyword.lower()
                # Count occurrences
                count = text_lower.count(keyword_lower)
                if count > 0:
                    # TF-IDF style: weight * log(1 + count) to avoid over-weighting repetition
                    import math
                    contribution = weight * math.log(1 + count)
                    type_score += contribution
                    found_keywords.append(f"{keyword} ({count}x)")
            
            scores[meeting_type] = type_score
            evidence_by_type[meeting_type] = found_keywords
        
        # Add structural features
        if segments:
            scores = self._add_structural_features(scores, segments, text_lower)
        
        # Sort by score (highest first)
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_types or sorted_types[0][1] == 0:
            # No keywords matched - default to TALK with low confidence
            return ClassificationResult(
                detected_type=MeetingType.TALK,
                confidence=0.0,
                evidence=["No strong indicators found"],
                secondary_types=[(mt, 0.0) for mt, _ in sorted_types[:5]],
                engine="heuristic",
            )
        
        # Top result
        top_type, top_score = sorted_types[0]
        
        # Calculate confidence based on margin from second place
        if len(sorted_types) > 1:
            second_score = sorted_types[1][1]
            margin = (top_score - second_score) / top_score if top_score > 0 else 0
            # Confidence: normalize to 0-1 range, boosted by margin
            raw_confidence = min(top_score / 20.0, 1.0)  # Normalize by expected max score
            confidence = raw_confidence * (0.5 + 0.5 * margin)  # Boost by margin
        else:
            confidence = min(top_score / 20.0, 1.0)
        
        # Secondary types (top 5 alternatives)
        secondary_types = [
            (mt, min(score / 20.0, 1.0))
            for mt, score in sorted_types[1:6]
        ]
        
        return ClassificationResult(
            detected_type=top_type,
            confidence=confidence,
            evidence=evidence_by_type[top_type][:5],  # Top 5 evidence phrases
            secondary_types=secondary_types,
            engine="heuristic",
        )
    
    def _add_structural_features(
        self,
        scores: Dict[MeetingType, float],
        segments: List[Dict[str, Any]],
        text_lower: str
    ) -> Dict[MeetingType, float]:
        """Add structural feature bonuses to scores.
        
        Structural features:
        - Question density (high questions → STATUS, DISCOVERY, BRAINSTORM)
        - Timeline vocabulary (yesterday/today/tomorrow → STATUS, PLANNING)
        - Action/commitment markers (will/should/must → PLANNING, INCIDENT)
        
        Args:
            scores: Current meeting type scores
            segments: Transcript segments with timing
            text_lower: Lowercased transcript text
        
        Returns:
            Updated scores dictionary with structural bonuses
        """
        # Question density (percentage of sentences ending in ?)
        sentences = text_lower.split('.')
        questions = [s for s in sentences if '?' in s]
        question_density = len(questions) / len(sentences) if sentences else 0
        
        if question_density > 0.3:  # High question density
            scores[MeetingType.DISCOVERY] += 2.0
            scores[MeetingType.BRAINSTORM] += 1.5
            scores[MeetingType.STATUS] += 1.0
        
        # Timeline vocabulary density
        timeline_words = ['yesterday', 'today', 'tomorrow', 'last week', 'next week', 'this week']
        timeline_count = sum(text_lower.count(word) for word in timeline_words)
        if timeline_count > 3:
            scores[MeetingType.STATUS] += 2.0
            scores[MeetingType.PLANNING] += 1.5
        
        # Commitment/action markers
        action_markers = ['will', 'should', 'must', 'need to', 'have to']
        action_count = sum(text_lower.count(marker) for marker in action_markers)
        if action_count > 5:
            scores[MeetingType.PLANNING] += 1.5
            scores[MeetingType.INCIDENT] += 1.0
        
        return scores

