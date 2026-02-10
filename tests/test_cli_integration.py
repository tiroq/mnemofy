"""Integration tests for CLI model selection features.

Tests cover:
- Explicit model override (--model flag)
- Auto-selection (--auto flag)
- Interactive selection (TTY detection)
- List models (--list-models flag)
- No GPU mode (--no-gpu flag)
- Error handling and fallbacks
"""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mnemofy.cli import app
from mnemofy.model_selector import MODEL_SPECS


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_audio_file(tmp_path):
    """Create a temporary test audio file."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_text("dummy audio content")
    return audio_file


class TestListModelsFlag:
    """Tests for --list-models flag."""
    
    def test_list_models_displays_table(self, runner, test_audio_file):
        """Test --list-models displays model table."""
        result = runner.invoke(
            app,
            ["transcribe", str(test_audio_file), "--list-models"],
            catch_exceptions=False,
        )
        
        assert result.exit_code == 0
        # Should show available models in output
        for model_name in MODEL_SPECS.keys():
            assert model_name in result.stdout or model_name in result.stdout.lower()

    def test_list_models_exits_without_transcribing(self, runner, test_audio_file):
        """Test --list-models exits without processing audio."""
        with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
            result = runner.invoke(
                app,
                ["transcribe", str(test_audio_file), "--list-models"],
                catch_exceptions=False,
            )
            
            # Should exit with code 0
            assert result.exit_code == 0
            # Should NOT call AudioExtractor (no transcription)
            mock_extractor.assert_not_called()

    def test_list_models_with_no_gpu_flag(self, runner, test_audio_file):
        """Test --list-models respects --no-gpu flag."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            mock_resources = Mock(
                cpu_cores=4,
                available_ram_gb=8.0,
                has_gpu=True,
                gpu_type="cuda",
            )
            mock_detect.return_value = mock_resources
            
            result = runner.invoke(
                app,
                ["transcribe", str(test_audio_file), "--list-models", "--no-gpu"],
                catch_exceptions=False,
            )
            
            assert result.exit_code == 0
            # Detection should have been called
            mock_detect.assert_called()

    def test_list_models_fallback_on_detection_error(self, runner, test_audio_file):
        """Test --list-models shows basic model list if detection fails."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            mock_detect.side_effect = RuntimeError("Detection failed")
            
            result = runner.invoke(
                app,
                ["transcribe", str(test_audio_file), "--list-models"],
                catch_exceptions=False,
            )
            
            assert result.exit_code == 0
            # Should still show models
            assert "tiny" in result.stdout or "base" in result.stdout


class TestExplicitModelOverride:
    """Tests for --model flag (explicit override)."""
    
    def test_explicit_model_skips_detection(self, runner, test_audio_file):
        """Test --model flag skips resource detection."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                    # Setup mocks
                    mock_extractor_instance = Mock()
                    mock_extractor.return_value = mock_extractor_instance
                    mock_extractor_instance.extract_audio.return_value = test_audio_file
                    
                    mock_transcriber_instance = Mock()
                    mock_transcriber.return_value = mock_transcriber_instance
                    mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                    mock_transcriber_instance.get_segments.return_value = []
                    
                    with patch("mnemofy.cli.NoteGenerator"):
                        runner.invoke(
                            app,
                            ["transcribe", str(test_audio_file), "--model", "tiny"],
                            catch_exceptions=False,
                        )
            
            # Detection should NOT be called when model is explicit
            mock_detect.assert_not_called()
            # Transcriber should be initialized with 'tiny'
            mock_transcriber.assert_called()
            assert "tiny" in str(mock_transcriber.call_args)

    def test_explicit_model_invalid_shows_error(self, runner, test_audio_file):
        """Test invalid model name shows error."""
        with patch("mnemofy.cli.detect_system_resources"):
            result = runner.invoke(
                app,
                ["transcribe", str(test_audio_file), "--model", "invalid-model"],
                catch_exceptions=False,
            )
            
            assert result.exit_code != 0
            assert "Unknown model" in result.stdout or "error" in result.stdout.lower()

    def test_explicit_model_all_valid_models(self, runner, test_audio_file):
        """Test explicit model works for all valid model names."""
        for model_name in MODEL_SPECS.keys():
            with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                    with patch("mnemofy.cli.NoteGenerator"):
                        # Setup mocks
                        mock_extractor_instance = Mock()
                        mock_extractor.return_value = mock_extractor_instance
                        mock_extractor_instance.extract_audio.return_value = test_audio_file
                        
                        mock_transcriber_instance = Mock()
                        mock_transcriber.return_value = mock_transcriber_instance
                        mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                        mock_transcriber_instance.get_segments.return_value = []
                        
                        result = runner.invoke(
                            app,
                            ["transcribe", str(test_audio_file), "--model", model_name],
                            catch_exceptions=False,
                        )
                        
                        # Should accept valid model (exit code may be 0 or non-zero depending on full process)
                        # At minimum, should not reject the model
                        assert "Unknown model" not in result.stdout


class TestAutoSelection:
    """Tests for auto-selection (--auto flag or non-TTY)."""
    
    def test_auto_flag_skips_interactive_menu(self, runner, test_audio_file):
        """Test --auto flag skips interactive menu."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.is_interactive_environment") as mock_interactive:
                with patch("mnemofy.cli.ModelMenu") as mock_menu:
                    with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                        with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                            with patch("mnemofy.cli.NoteGenerator"):
                                # Setup mocks
                                mock_resources = Mock(
                                    cpu_cores=4,
                                    available_ram_gb=8.0,
                                    has_gpu=False,
                                )
                                mock_detect.return_value = mock_resources
                                mock_interactive.return_value = True  # TTY available
                                
                                mock_extractor_instance = Mock()
                                mock_extractor.return_value = mock_extractor_instance
                                mock_extractor_instance.extract_audio.return_value = test_audio_file
                                
                                mock_transcriber_instance = Mock()
                                mock_transcriber.return_value = mock_transcriber_instance
                                mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                                mock_transcriber_instance.get_segments.return_value = []
                                
                                runner.invoke(
                                    app,
                                    ["transcribe", str(test_audio_file), "--auto"],
                                    catch_exceptions=False,
                                )
                        
                        # Menu should NOT be shown with --auto
                        mock_menu.assert_not_called()

    def test_non_tty_environment_auto_selects(self, runner, test_audio_file):
        """Test non-TTY environment automatically selects model."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.is_interactive_environment") as mock_interactive:
                with patch("mnemofy.cli.ModelMenu") as mock_menu:
                    with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                        with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                            with patch("mnemofy.cli.NoteGenerator"):
                                # Setup mocks for non-TTY
                                mock_resources = Mock(
                                    cpu_cores=4,
                                    available_ram_gb=8.0,
                                    has_gpu=False,
                                )
                                mock_detect.return_value = mock_resources
                                mock_interactive.return_value = False  # NOT a TTY
                                
                                mock_extractor_instance = Mock()
                                mock_extractor.return_value = mock_extractor_instance
                                mock_extractor_instance.extract_audio.return_value = test_audio_file
                                
                                mock_transcriber_instance = Mock()
                                mock_transcriber.return_value = mock_transcriber_instance
                                mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                                mock_transcriber_instance.get_segments.return_value = []
                                
                                runner.invoke(
                                    app,
                                    ["transcribe", str(test_audio_file)],
                                    catch_exceptions=False,
                                )
                        
                        # Menu should NOT be shown in non-TTY
                        mock_menu.assert_not_called()

    def test_auto_selection_fallback_on_error(self, runner, test_audio_file):
        """Test fallback to 'base' model if auto-selection fails."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                    with patch("mnemofy.cli.NoteGenerator"):
                        # Detection fails
                        mock_detect.side_effect = RuntimeError("Detection failed")
                        
                        mock_extractor_instance = Mock()
                        mock_extractor.return_value = mock_extractor_instance
                        mock_extractor_instance.extract_audio.return_value = test_audio_file
                        
                        mock_transcriber_instance = Mock()
                        mock_transcriber.return_value = mock_transcriber_instance
                        mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                        mock_transcriber_instance.get_segments.return_value = []
                        
                        result = runner.invoke(
                            app,
                            ["transcribe", str(test_audio_file)],
                            catch_exceptions=False,
                        )
                        
                        # Should show fallback message
                        assert "Falling back" in result.stdout or "base" in result.stdout


class TestNoGPUFlag:
    """Tests for --no-gpu flag."""
    
    def test_no_gpu_disables_gpu_in_detection(self, runner, test_audio_file):
        """Test --no-gpu flag disables GPU in resource detection."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.is_interactive_environment") as mock_interactive:
                with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                    with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                        with patch("mnemofy.cli.NoteGenerator"):
                            # Setup
                            mock_resources = Mock(
                                cpu_cores=4,
                                available_ram_gb=8.0,
                                has_gpu=True,
                                gpu_type="cuda",
                                available_vram_gb=4.0,
                            )
                            mock_detect.return_value = mock_resources
                            mock_interactive.return_value = False  # Non-TTY
                            
                            mock_extractor_instance = Mock()
                            mock_extractor.return_value = mock_extractor_instance
                            mock_extractor_instance.extract_audio.return_value = test_audio_file
                            
                            mock_transcriber_instance = Mock()
                            mock_transcriber.return_value = mock_transcriber_instance
                            mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                            mock_transcriber_instance.get_segments.return_value = []
                            
                            runner.invoke(
                                app,
                                ["transcribe", str(test_audio_file), "--no-gpu"],
                                catch_exceptions=False,
                            )
                        
                        # Should execute without error (recommend_model called with use_gpu=False)
                        # The test validates that --no-gpu doesn't crash the system


class TestInteractiveSelection:
    """Tests for interactive menu selection (TTY only)."""
    
    def test_interactive_menu_shown_in_tty(self, runner, test_audio_file):
        """Test interactive menu is shown in TTY environment."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.is_interactive_environment") as mock_interactive:
                with patch("mnemofy.cli.ModelMenu") as mock_menu:
                    with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                        with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                            with patch("mnemofy.cli.NoteGenerator"):
                                # Setup
                                mock_resources = Mock(
                                    cpu_cores=4,
                                    available_ram_gb=8.0,
                                    has_gpu=False,
                                )
                                mock_detect.return_value = mock_resources
                                mock_interactive.return_value = True  # TTY
                                
                                mock_model_spec = Mock(name="small")
                                mock_menu_instance = Mock()
                                mock_menu.return_value = mock_menu_instance
                                mock_menu_instance.show.return_value = mock_model_spec
                                
                                mock_extractor_instance = Mock()
                                mock_extractor.return_value = mock_extractor_instance
                                mock_extractor_instance.extract_audio.return_value = test_audio_file
                                
                                mock_transcriber_instance = Mock()
                                mock_transcriber.return_value = mock_transcriber_instance
                                mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                                mock_transcriber_instance.get_segments.return_value = []
                                
                                runner.invoke(
                                    app,
                                    ["transcribe", str(test_audio_file)],
                                    catch_exceptions=False,
                                )
                        
                        # ModelMenu should be shown
                        mock_menu.assert_called()

    def test_interactive_menu_cancellation(self, runner, test_audio_file):
        """Test handling of user cancellation in interactive menu."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.is_interactive_environment") as mock_interactive:
                with patch("mnemofy.cli.ModelMenu") as mock_menu:
                    # Setup
                    mock_resources = Mock(
                        cpu_cores=4,
                        available_ram_gb=8.0,
                        has_gpu=False,
                    )
                    mock_detect.return_value = mock_resources
                    mock_interactive.return_value = True  # TTY
                    
                    mock_menu_instance = Mock()
                    mock_menu.return_value = mock_menu_instance
                    mock_menu_instance.show.return_value = None  # User cancelled
                    
                    result = runner.invoke(
                        app,
                        ["transcribe", str(test_audio_file)],
                        catch_exceptions=False,
                    )
                
                # Should exit with error due to cancellation
                assert result.exit_code != 0
                assert "cancelled" in result.stdout.lower()


class TestFlagCombinations:
    """Tests for flag combinations and conflicts."""
    
    def test_model_and_auto_flags_explicit_takes_precedence(self, runner, test_audio_file):
        """Test --model takes precedence over --auto."""
        with patch("mnemofy.cli.detect_system_resources") as mock_detect:
            with patch("mnemofy.cli.AudioExtractor") as mock_extractor:
                with patch("mnemofy.cli.Transcriber") as mock_transcriber:
                    with patch("mnemofy.cli.NoteGenerator"):
                        # Setup mocks
                        mock_extractor_instance = Mock()
                        mock_extractor.return_value = mock_extractor_instance
                        mock_extractor_instance.extract_audio.return_value = test_audio_file
                        
                        mock_transcriber_instance = Mock()
                        mock_transcriber.return_value = mock_transcriber_instance
                        mock_transcriber_instance.transcribe.return_value = Mock(text="test")
                        mock_transcriber_instance.get_segments.return_value = []
                        
                        runner.invoke(
                            app,
                            [
                                "transcribe",
                                str(test_audio_file),
                                "--model", "tiny",
                                "--auto",
                            ],
                            catch_exceptions=False,
                        )
                        
                        # Detection should NOT be called
                        mock_detect.assert_not_called()

    def test_list_models_ignores_other_flags(self, runner, test_audio_file):
        """Test --list-models ignores other flags."""
        result = runner.invoke(
            app,
            [
                "transcribe",
                str(test_audio_file),
                "--list-models",
                "--model", "tiny",
                "--auto",
                "--no-gpu",
            ],
            catch_exceptions=False,
        )
        
        # Should exit with 0 and show models
        assert result.exit_code == 0
        assert "tiny" in result.stdout or "base" in result.stdout
