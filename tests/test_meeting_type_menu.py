"""Tests for interactive meeting type menu."""

import sys
from unittest.mock import Mock, patch
import pytest

from mnemofy.classifier import MeetingType, ClassificationResult
from mnemofy.tui.meeting_type_menu import MeetingTypeMenu, select_meeting_type


class TestMeetingTypeMenu:
    """Test meeting type menu rendering and interaction."""
    
    def test_menu_initialization(self):
        """Should initialize menu with classification result."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=["standup", "updates"],
            secondary_types=[
                (MeetingType.PLANNING, 0.65),
                (MeetingType.DESIGN, 0.45),
            ],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        
        assert menu.detected_type == MeetingType.STATUS
        assert menu.confidence == 0.85
        assert len(menu.candidates) >= 3  # detected + 2 secondary
        assert menu.candidates[0][0] == MeetingType.STATUS
        assert menu.selected_index == 0  # Start with detected type
    
    def test_menu_fills_candidates(self):
        """Should fill candidates list to at least 6 types."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=["standup"],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        
        assert len(menu.candidates) >= 6
        assert menu.candidates[0][0] == MeetingType.STATUS
    
    def test_menu_confidence_colors(self):
        """Should use appropriate colors for confidence levels."""
        menu = MeetingTypeMenu(
            ClassificationResult(
                detected_type=MeetingType.STATUS,
                confidence=0.9,
                evidence=[],
                secondary_types=[],
                engine="heuristic"
            )
        )
        
        assert menu._get_confidence_color(0.9) == "green"
        assert menu._get_confidence_color(0.55) == "yellow"
        assert menu._get_confidence_color(0.4) == "red"
    
    def test_type_descriptions(self):
        """Should provide descriptions for all meeting types."""
        menu = MeetingTypeMenu(
            ClassificationResult(
                detected_type=MeetingType.STATUS,
                confidence=0.85,
                evidence=[],
                secondary_types=[],
                engine="heuristic"
            )
        )
        
        for mt in MeetingType:
            desc = menu._get_type_description(mt)
            assert isinstance(desc, str)
            assert len(desc) > 0
    
    @patch('mnemofy.tui.meeting_type_menu.readchar.readkey')
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_menu_navigation_down(self, mock_console_class, mock_readkey):
        """Should navigate down through menu options."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=[],
            secondary_types=[(MeetingType.PLANNING, 0.65)],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        
        # Simulate DOWN key then ENTER
        mock_readkey.side_effect = [
            '\x1b[B',  # DOWN arrow
            '\r',      # ENTER
        ]
        
        # This would fail because readkey returns different values
        # Let's use the actual readchar.key constants
        from readchar import key
        mock_readkey.side_effect = [key.DOWN, key.ENTER]
        
        selected = menu.show()
        
        # Should have moved to next item
        assert selected == menu.candidates[1][0]
    
    @patch('mnemofy.tui.meeting_type_menu.readchar.readkey')
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_menu_escape_returns_recommended(self, mock_console_class, mock_readkey):
        """Should return recommended type when ESC pressed."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        
        from readchar import key
        mock_readkey.return_value = key.ESC
        
        selected = menu.show()
        
        assert selected == MeetingType.STATUS  # Should return detected type
    
    @patch('mnemofy.tui.meeting_type_menu.readchar.readkey')
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_menu_ctrl_c_returns_recommended(self, mock_console_class, mock_readkey):
        """Should handle Ctrl+C gracefully."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        
        # Simulate Ctrl+C
        mock_readkey.side_effect = KeyboardInterrupt()
        
        selected = menu.show()
        
        assert selected == MeetingType.STATUS  # Should return detected type on interrupt


class TestSelectMeetingType:
    """Test the select_meeting_type helper function."""
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=False)
    def test_auto_accept_when_not_tty(self, mock_isatty):
        """Should auto-accept when not in TTY."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.55,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        selected = select_meeting_type(result, interactive=True)
        
        assert selected == MeetingType.STATUS
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.sys.stdout.isatty', return_value=True)
    def test_auto_accept_when_not_interactive(self, mock_stdout, mock_stdin):
        """Should auto-accept when interactive=False."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.55,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        selected = select_meeting_type(result, interactive=False)
        
        assert selected == MeetingType.STATUS
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.sys.stdout.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.MeetingTypeMenu')
    def test_shows_menu_in_tty_with_interactive(self, mock_menu_class, mock_stdout, mock_stdin):
        """Should show menu when in TTY and interactive=True."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.55,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        mock_menu = Mock()
        mock_menu.show.return_value = MeetingType.PLANNING
        mock_menu_class.return_value = mock_menu
        
        selected = select_meeting_type(result, interactive=True)
        
        # Menu should be created and shown
        mock_menu_class.assert_called_once()
        mock_menu.show.assert_called_once()
        assert selected == MeetingType.PLANNING
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.sys.stdout.isatty', return_value=True)
    def test_auto_accept_perfect_confidence(self, mock_stdout, mock_stdin):
        """Should auto-accept when confidence is 1.0."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=1.0,
            evidence=["perfect match"],
            secondary_types=[],
            engine="heuristic"
        )
        
        selected = select_meeting_type(result, interactive=True)
        
        assert selected == MeetingType.STATUS
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.sys.stdout.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.MeetingTypeMenu')
    def test_uses_auto_accept_threshold(self, mock_menu_class, mock_stdout, mock_stdin):
        """Should respect auto_accept_threshold parameter."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.75,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        mock_menu = Mock()
        mock_menu.show.return_value = MeetingType.STATUS
        mock_menu_class.return_value = mock_menu
        
        # With threshold 0.8, should show menu for 0.75
        selected = select_meeting_type(
            result,
            auto_accept_threshold=0.8,
            interactive=True
        )
        
        # Menu should be shown
        mock_menu_class.assert_called_once()
    
    @patch('mnemofy.tui.meeting_type_menu.sys.stdin.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.sys.stdout.isatty', return_value=True)
    @patch('mnemofy.tui.meeting_type_menu.MeetingTypeMenu')
    def test_handles_menu_returning_none(self, mock_menu_class, mock_stdout, mock_stdin):
        """Should use recommended type if menu returns None."""
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.55,
            evidence=[],
            secondary_types=[],
            engine="heuristic"
        )
        
        mock_menu = Mock()
        mock_menu.show.return_value = None
        mock_menu_class.return_value = mock_menu
        
        selected = select_meeting_type(result, interactive=True)
        
        assert selected == MeetingType.STATUS  # Fallback to detected type


class TestMenuConfidenceBehavior:
    """Test confidence-based menu behavior."""
    
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_high_confidence_message(self, mock_console_class):
        """Should show appropriate message for high confidence."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.85,
            evidence=["standup"],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        # Render to check messages (would need to inspect output)
        menu._render_menu()
        
        # Menu rendered without errors
        assert mock_console.print.called
    
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_medium_confidence_message(self, mock_console_class):
        """Should show warning for medium confidence."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.55,
            evidence=["maybe"],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        menu._render_menu()
        
        assert mock_console.print.called
    
    @patch('mnemofy.tui.meeting_type_menu.Console')
    def test_low_confidence_message(self, mock_console_class):
        """Should show strong warning for low confidence."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        result = ClassificationResult(
            detected_type=MeetingType.STATUS,
            confidence=0.35,
            evidence=["unclear"],
            secondary_types=[],
            engine="heuristic"
        )
        
        menu = MeetingTypeMenu(result)
        menu._render_menu()
        
        assert mock_console.print.called
