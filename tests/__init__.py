"""Test package initialization."""

import mnemofy


def test_version() -> None:
    """Test that version is defined."""
    assert hasattr(mnemofy, "__version__")
    assert isinstance(mnemofy.__version__, str)
    assert mnemofy.__version__ == "0.1.0"
