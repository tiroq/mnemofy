"""Interactive meeting type selection menu.

Displays detected meeting type with confidence score and allows users to
override the selection if needed using arrow key navigation.
"""

import sys
import logging
from typing import Optional, List, Tuple

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import readchar

from mnemofy.classifier import MeetingType, ClassificationResult

logger = logging.getLogger(__name__)


class MeetingTypeMenu:
    """Interactive menu for selecting or confirming meeting type.
    
    Displays the detected meeting type with confidence and allows user to
    override the selection. Behavior adapts based on confidence level:
    - High confidence (≥0.6): Brief confirmation, quick to accept
    - Medium confidence (0.5-0.6): Warning with option to override
    - Low confidence (<0.5): Emphasize alternatives, encourage selection
    """
    
    def __init__(
        self,
        classification_result: ClassificationResult,
        all_types: Optional[List[MeetingType]] = None,
    ):
        """Initialize the meeting type menu.
        
        Args:
            classification_result: Detection result with type, confidence, evidence
            all_types: All available meeting types (default: all 9 types)
        """
        self.result = classification_result
        self.detected_type = classification_result.detected_type
        self.confidence = classification_result.confidence
        self.evidence = classification_result.evidence
        self.secondary_types = classification_result.secondary_types
        
        # Build candidates list: detected + top 5 alternatives
        self.candidates: List[Tuple[MeetingType, float]] = []
        self.candidates.append((self.detected_type, self.confidence))
        
        # Add secondary types
        for mt, score in self.secondary_types[:5]:
            if mt != self.detected_type:
                self.candidates.append((mt, score))
        
        # Fill with remaining types if < 6 candidates
        if all_types is None:
            all_types = list(MeetingType)
        
        existing_types = {mt for mt, _ in self.candidates}
        for mt in all_types:
            if mt not in existing_types and len(self.candidates) < 6:
                self.candidates.append((mt, 0.0))
        
        self.selected_index = 0  # Start with detected type selected
        self.console = Console()
        
        logger.debug(
            f"MeetingTypeMenu initialized: detected={self.detected_type.value}, "
            f"confidence={self.confidence:.2f}, candidates={len(self.candidates)}"
        )
    
    def show(self) -> Optional[MeetingType]:
        """Display interactive menu and return selected meeting type.
        
        Returns:
            Selected MeetingType or None if cancelled
        """
        try:
            return self._run_menu_loop()
        except KeyboardInterrupt:
            logger.info("Meeting type selection cancelled by user (Ctrl+C)")
            self.console.print("\n[yellow]Selection cancelled - using recommended type[/yellow]")
            return self.detected_type
    
    def _run_menu_loop(self) -> Optional[MeetingType]:
        """Run the interactive menu loop with keyboard navigation."""
        while True:
            # Clear and redraw
            self.console.clear()
            self._render_menu()
            
            # Read key
            key = readchar.readkey()
            
            if key == readchar.key.UP:
                self.selected_index = (self.selected_index - 1) % len(self.candidates)
            elif key == readchar.key.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.candidates)
            elif key == readchar.key.ENTER:
                selected_type = self.candidates[self.selected_index][0]
                logger.info(f"User selected meeting type: {selected_type.value}")
                return selected_type
            elif key == readchar.key.ESC:
                logger.info("User cancelled selection, using recommended type")
                return self.detected_type
            elif key == readchar.key.CTRL_C:
                raise KeyboardInterrupt()
    
    def _render_menu(self) -> None:
        """Render the menu with current selection state."""
        # Title with confidence indicator
        confidence_pct = self.confidence * 100
        confidence_color = self._get_confidence_color(self.confidence)
        
        title = Text()
        title.append("Meeting Type Detection\n", style="bold cyan")
        title.append(f"Confidence: ", style="dim")
        title.append(f"{confidence_pct:.1f}%", style=f"bold {confidence_color}")
        
        # Add confidence message
        if self.confidence >= 0.6:
            title.append("\n✓ High confidence - accept or choose alternative", style="dim green")
        elif self.confidence >= 0.5:
            title.append("\n⚠ Medium confidence - review alternatives", style="dim yellow")
        else:
            title.append("\n⚠ Low confidence - please review carefully", style="dim red")
        
        # Build table
        table = Table(show_header=True, show_edge=False, pad_edge=False, box=None)
        table.add_column("", width=2)
        table.add_column("Type", style="cyan")
        table.add_column("Score", justify="right", width=8)
        table.add_column("Description", style="dim")
        
        for i, (meeting_type, score) in enumerate(self.candidates):
            # Selection indicator
            if i == self.selected_index:
                indicator = "→"
            else:
                indicator = " "
            
            # Type name with recommended marker
            type_text = Text(meeting_type.value)
            if i == 0:
                type_text.append(" (recommended)", style="dim green")
            
            # Score
            score_text = f"{score * 100:.1f}%" if score > 0 else "—"
            
            # Description
            description = self._get_type_description(meeting_type)
            
            table.add_row(
                indicator,
                type_text,
                score_text,
                description
            )
        
        # Evidence section (show top 3)
        evidence_text = Text()
        if self.evidence:
            evidence_text.append("\nEvidence: ", style="dim")
            evidence_text.append(", ".join(self.evidence[:3]), style="italic dim")
        
        # Instructions
        instructions = Text()
        instructions.append("\n↑↓ ", style="bold cyan")
        instructions.append("Navigate  ", style="dim")
        instructions.append("Enter ", style="bold cyan")
        instructions.append("Select  ", style="dim")
        instructions.append("Esc ", style="bold cyan")
        instructions.append("Use recommended", style="dim")
        
        # Render panel with all components
        content = Group(
            table,
            evidence_text,
            instructions
        )
        
        panel = Panel(
            content,
            title=title,
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence level."""
        if confidence >= 0.6:
            return "green"
        elif confidence >= 0.5:
            return "yellow"
        else:
            return "red"
    
    def _get_type_description(self, meeting_type: MeetingType) -> str:
        """Get short description for each meeting type."""
        descriptions = {
            MeetingType.STATUS: "Daily standup, progress sync",
            MeetingType.PLANNING: "Sprint planning, roadmap",
            MeetingType.DESIGN: "Technical design, architecture",
            MeetingType.DEMO: "Feature demo, showcase",
            MeetingType.TALK: "Presentation, lecture",
            MeetingType.INCIDENT: "Incident response, RCA",
            MeetingType.DISCOVERY: "User research, requirements",
            MeetingType.ONEONONE: "1:1 check-in, feedback",
            MeetingType.BRAINSTORM: "Ideation, creative session",
        }
        return descriptions.get(meeting_type, "")


def select_meeting_type(
    classification_result: ClassificationResult,
    auto_accept_threshold: float = 0.6,
    interactive: bool = True,
) -> MeetingType:
    """Select meeting type with optional interactive menu.
    
    Args:
        classification_result: Detection result from classifier
        auto_accept_threshold: Auto-accept if confidence >= this (default: 0.6)
        interactive: Show menu if True and in TTY (default: True)
    
    Returns:
        Selected meeting type (detected or user override)
    """
    # Auto-accept if confidence meets threshold
    if classification_result.confidence >= auto_accept_threshold:
        logger.debug(
            f"Auto-accepting detected type (confidence {classification_result.confidence:.2f} >= {auto_accept_threshold})"
        )
        return classification_result.detected_type
    
    # Check if we should show menu
    should_show_menu = (
        interactive
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    )
    
    if not should_show_menu:
        logger.debug(
            f"Auto-accepting detected type: interactive={interactive}, "
            f"tty={sys.stdin.isatty()}"
        )
        return classification_result.detected_type
    
    # Show interactive menu
    menu = MeetingTypeMenu(classification_result)
    selected = menu.show()
    
    if selected is None:
        logger.info("Menu cancelled, using recommended type")
        return classification_result.detected_type
    
    return selected
