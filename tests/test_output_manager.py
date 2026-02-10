"""Tests for OutputManager path management."""

import pytest
import tempfile
from pathlib import Path

from mnemofy.output_manager import OutputManager


class TestOutputManagerBasics:
    """Basic OutputManager functionality tests."""
    
    def test_init_with_existing_file(self, tmp_path):
        """Test initialization with existing input file."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.input_path == input_file
    
    def test_init_with_string_path(self, tmp_path):
        """Test initialization with string path (not Path object)."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(str(input_file))
        assert manager.input_path == input_file
    
    def test_init_with_path_object(self, tmp_path):
        """Test initialization with Path object."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert isinstance(manager.input_path, Path)
        assert manager.input_path == input_file
    
    def test_input_file_not_found(self, tmp_path):
        """Test that FileNotFoundError raised for missing input."""
        input_file = tmp_path / "nonexistent.mp4"
        
        with pytest.raises(FileNotFoundError):
            OutputManager(input_file)
    
    def test_basename_extraction(self, tmp_path):
        """Test that basename is extracted correctly."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "meeting"
    
    def test_basename_with_dots(self, tmp_path):
        """Test basename extraction with multiple dots."""
        input_file = tmp_path / "my.meeting.final.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "my.meeting.final"


class TestOutputManagerDefaultOutdir:
    """Tests for default output directory behavior."""
    
    def test_default_outdir_is_input_parent(self, tmp_path):
        """Test that default outdir is input file's parent directory."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.outdir == tmp_path
    
    def test_default_outdir_with_nested_input(self, tmp_path):
        """Test default outdir with nested input directory."""
        nested_dir = tmp_path / "videos" / "archive"
        nested_dir.mkdir(parents=True)
        input_file = nested_dir / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.outdir == nested_dir


class TestOutputManagerCustomOutdir:
    """Tests for custom output directory behavior."""
    
    def test_custom_outdir_absolute_path(self, tmp_path):
        """Test with custom absolute output directory."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        outdir.mkdir()
        
        manager = OutputManager(input_file, outdir=outdir)
        assert manager.outdir == outdir
    
    def test_custom_outdir_relative_path(self, tmp_path, monkeypatch):
        """Test with custom relative output directory."""
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)
        
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file, outdir="output")
        assert manager.outdir == (tmp_path / "output").resolve()
    
    def test_custom_outdir_string_path(self, tmp_path):
        """Test with custom outdir as string."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        
        manager = OutputManager(input_file, outdir=str(outdir))
        assert manager.outdir == outdir
    
    def test_custom_outdir_path_object(self, tmp_path):
        """Test with custom outdir as Path object."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        
        manager = OutputManager(input_file, outdir=outdir)
        assert manager.outdir == outdir


class TestOutputManagerOutdirCreation:
    """Tests for output directory creation."""
    
    def test_creates_nonexistent_outdir(self, tmp_path):
        """Test that nonexistent outdir is created."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "new_dir"
        
        assert not outdir.exists()
        manager = OutputManager(input_file, outdir=outdir)
        assert outdir.exists()
    
    def test_creates_nested_outdir(self, tmp_path):
        """Test that nested nonexistent directories are created."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "a" / "b" / "c"
        
        assert not outdir.exists()
        manager = OutputManager(input_file, outdir=outdir)
        assert outdir.exists()
    
    def test_outdir_already_exists(self, tmp_path):
        """Test with existing output directory."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        outdir.mkdir()
        
        manager = OutputManager(input_file, outdir=outdir)
        assert manager.outdir == outdir
    
    def test_outdir_is_file_not_directory(self, tmp_path):
        """Test error when outdir path is a file."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir_file = tmp_path / "not_a_dir"
        outdir_file.touch()
        
        with pytest.raises(ValueError, match="not a directory"):
            OutputManager(input_file, outdir=outdir_file)


class TestOutputManagerOutdirPermissions:
    """Tests for output directory permissions validation."""
    
    def test_nonwritable_outdir(self, tmp_path):
        """Test error when output directory is not writable."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "readonly"
        outdir.mkdir()
        
        # Make directory read-only (Unix only)
        try:
            outdir.chmod(0o444)
            with pytest.raises(PermissionError):
                OutputManager(input_file, outdir=outdir)
        finally:
            # Restore write permission for cleanup
            outdir.chmod(0o755)


class TestOutputManagerPaths:
    """Tests for output path generation."""
    
    def test_get_audio_path(self, tmp_path):
        """Test audio path generation."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        audio_path = manager.get_audio_path()
        
        assert audio_path == tmp_path / "meeting.mnemofy.wav"
        assert audio_path.name == "meeting.mnemofy.wav"
    
    def test_get_audio_path_preserves_basename(self, tmp_path):
        """Test that audio path preserves input basename."""
        input_file = tmp_path / "my_meeting_final.mkv"
        input_file.touch()
        
        manager = OutputManager(input_file)
        audio_path = manager.get_audio_path()
        
        assert "my_meeting_final" in str(audio_path)
        assert audio_path.name == "my_meeting_final.mnemofy.wav"
    
    def test_get_transcript_paths(self, tmp_path):
        """Test transcript paths generation for all formats."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        paths = manager.get_transcript_paths()
        
        assert 'txt' in paths
        assert 'srt' in paths
        assert 'json' in paths
        assert paths['txt'] == tmp_path / "meeting.transcript.txt"
        assert paths['srt'] == tmp_path / "meeting.transcript.srt"
        assert paths['json'] == tmp_path / "meeting.transcript.json"
    
    def test_transcript_paths_are_different(self, tmp_path):
        """Test that all transcript paths are different."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        paths = manager.get_transcript_paths()
        
        # All paths should be different
        assert paths['txt'] != paths['srt']
        assert paths['txt'] != paths['json']
        assert paths['srt'] != paths['json']
    
    def test_get_notes_path(self, tmp_path):
        """Test notes path generation."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        notes_path = manager.get_notes_path()
        
        assert notes_path == tmp_path / "meeting.notes.md"
        assert notes_path.name == "meeting.notes.md"


class TestOutputManagerPathsWithCustomOutdir:
    """Tests for path generation with custom output directory."""
    
    def test_all_paths_in_custom_outdir(self, tmp_path):
        """Test that all paths are in the custom outdir."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        
        manager = OutputManager(input_file, outdir=outdir)
        
        audio_path = manager.get_audio_path()
        transcript_paths = manager.get_transcript_paths()
        notes_path = manager.get_notes_path()
        
        assert audio_path.parent == outdir
        assert transcript_paths['txt'].parent == outdir
        assert transcript_paths['srt'].parent == outdir
        assert transcript_paths['json'].parent == outdir
        assert notes_path.parent == outdir
    
    def test_paths_use_basename_from_input(self, tmp_path):
        """Test that paths use basename from input, not outdir."""
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        outdir = tmp_path / "transcripts"
        
        manager = OutputManager(input_file, outdir=outdir)
        paths = manager.get_transcript_paths()
        
        # All should have "meeting" basename
        assert "meeting" in paths['txt'].name
        assert "meeting" in paths['srt'].name
        assert "meeting" in paths['json'].name


class TestOutputManagerVariousExtensions:
    """Tests with various input file extensions."""
    
    @pytest.mark.parametrize("extension", [
        "mp4", "mkv", "mov", "avi", "webm",
        "mp3", "wav", "flac", "aac", "ogg"
    ])
    def test_various_input_extensions(self, tmp_path, extension):
        """Test with various input file extensions."""
        input_file = tmp_path / f"input.{extension}"
        input_file.touch()
        
        manager = OutputManager(input_file)
        
        # Basename should not include extension
        assert manager.basename == "input"
        
        # Audio path should always be .mnemofy.wav
        assert manager.get_audio_path().suffix == ".wav"
        
        # Transcript paths should have correct suffixes
        paths = manager.get_transcript_paths()
        assert paths['txt'].suffix == ".txt"
        assert paths['srt'].suffix == ".srt"
        assert paths['json'].suffix == ".json"


class TestOutputManagerSpecialFilenames:
    """Tests with special characters in filenames."""
    
    def test_filename_with_spaces(self, tmp_path):
        """Test with spaces in filename."""
        input_file = tmp_path / "my meeting video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "my meeting video"
        assert "my meeting video" in manager.get_audio_path().name
    
    def test_filename_with_dots(self, tmp_path):
        """Test with multiple dots in filename."""
        input_file = tmp_path / "my.meeting.v2.final.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "my.meeting.v2.final"
    
    def test_filename_with_dashes(self, tmp_path):
        """Test with dashes in filename."""
        input_file = tmp_path / "my-meeting-2026-02-10.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "my-meeting-2026-02-10"


class TestOutputManagerHomeExpansion:
    """Tests for home directory expansion."""
    
    def test_tilde_expansion_input(self, tmp_path, monkeypatch):
        """Test ~ expansion in input path."""
        # Create a test file in home-like directory
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        # Mock expanduser to return our tmp_path
        import pathlib
        original_expanduser = pathlib.Path.expanduser
        
        def mock_expanduser(self):
            if str(self).startswith("~"):
                return tmp_path / str(self)[2:]
            return original_expanduser(self)
        
        try:
            monkeypatch.setattr(pathlib.Path, "expanduser", mock_expanduser)
            manager = OutputManager("~/video.mp4")
            assert manager.input_path.name == "video.mp4"
        finally:
            monkeypatch.setattr(pathlib.Path, "expanduser", original_expanduser)


class TestOutputManagerProperties:
    """Tests for OutputManager properties."""
    
    def test_outdir_property_returns_path(self, tmp_path):
        """Test that outdir property returns Path object."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert isinstance(manager.outdir, Path)
    
    def test_basename_property_returns_string(self, tmp_path):
        """Test that basename property returns string."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert isinstance(manager.basename, str)
    
    def test_input_path_property_returns_path(self, tmp_path):
        """Test that input_path property returns Path object."""
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert isinstance(manager.input_path, Path)


class TestOutputManagerIntegration:
    """Integration tests for OutputManager."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow with all path generation."""
        # Create input file
        input_file = tmp_path / "meeting.mp4"
        input_file.touch()
        
        # Create output directory
        outdir = tmp_path / "transcripts"
        
        # Initialize manager
        manager = OutputManager(input_file, outdir=outdir)
        
        # Get all paths
        audio_path = manager.get_audio_path()
        transcript_paths = manager.get_transcript_paths()
        notes_path = manager.get_notes_path()
        
        # Verify all paths
        assert audio_path.parent == outdir
        assert transcript_paths['txt'].parent == outdir
        assert transcript_paths['srt'].parent == outdir
        assert transcript_paths['json'].parent == outdir
        assert notes_path.parent == outdir
        
        # Verify all paths can be created (touch them)
        audio_path.touch()
        for path in transcript_paths.values():
            path.touch()
        notes_path.touch()
        
        # Verify files were created
        assert audio_path.exists()
        assert all(p.exists() for p in transcript_paths.values())
        assert notes_path.exists()
    
    def test_multiple_inputs_same_outdir(self, tmp_path):
        """Test multiple different input files writing to same outdir."""
        outdir = tmp_path / "transcripts"
        
        # First file
        file1 = tmp_path / "meeting1.mp4"
        file1.touch()
        manager1 = OutputManager(file1, outdir=outdir)
        
        # Second file
        file2 = tmp_path / "meeting2.mp4"
        file2.touch()
        manager2 = OutputManager(file2, outdir=outdir)
        
        # Both should use same outdir but different basenames
        assert manager1.outdir == outdir
        assert manager2.outdir == outdir
        assert manager1.basename != manager2.basename
        assert manager1.basename == "meeting1"
        assert manager2.basename == "meeting2"
        
        # Paths should be different
        assert manager1.get_audio_path() != manager2.get_audio_path()


class TestOutputManagerEdgeCases:
    """Edge case tests."""
    
    def test_single_character_basename(self, tmp_path):
        """Test with single character filename."""
        input_file = tmp_path / "a.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "a"
    
    def test_very_long_basename(self, tmp_path):
        """Test with very long filename."""
        long_name = "a" * 200 + ".mp4"
        input_file = tmp_path / long_name
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert len(manager.basename) == 200
    
    def test_numbers_only_basename(self, tmp_path):
        """Test with numbers-only filename."""
        input_file = tmp_path / "123456.mp4"
        input_file.touch()
        
        manager = OutputManager(input_file)
        assert manager.basename == "123456"

class TestOutputManagerErrorCases:
    """Test error handling edge cases for complete coverage."""
    
    def test_oserror_during_mkdir(self, tmp_path):
        """Test OSError raised during directory creation."""
        from unittest.mock import patch
        
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        # Mock mkdir to raise OSError
        with patch.object(Path, "mkdir", side_effect=OSError("Disk error")):
            with pytest.raises(ValueError, match="Cannot create output directory"):
                OutputManager(input_file, outdir="/some/nonexistent/path")
    
    def test_permission_error_during_mkdir(self, tmp_path):
        """Test PermissionError raised during directory creation."""
        from unittest.mock import patch
        
        input_file = tmp_path / "video.mp4"
        input_file.touch()
        
        # Mock mkdir to raise PermissionError
        with patch.object(Path, "mkdir", side_effect=PermissionError("No access")):
            with pytest.raises(PermissionError, match="Cannot create output directory"):
                OutputManager(input_file, outdir="/root/forbidden")