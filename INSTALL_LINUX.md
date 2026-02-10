# Linux Installation Guide for mnemofy

Complete installation instructions for mnemofy on Linux systems.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Install (Recommended)](#quick-install-recommended)
- [Distribution-Specific Instructions](#distribution-specific-instructions)
  - [Ubuntu/Debian/Mint](#ubuntudebianmint)
  - [Fedora/RHEL/CentOS](#fedorarhelcentos)
  - [Arch Linux/Manjaro](#arch-linuxmanjaro)
  - [openSUSE](#opensuse)
- [Installation Methods](#installation-methods)
  - [Method 1: pipx (Recommended)](#method-1-pipx-recommended)
  - [Method 2: pip (User Install)](#method-2-pip-user-install)
  - [Method 3: From Source](#method-3-from-source)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

- **Python**: 3.9 or higher (3.12+ recommended)
- **RAM**: Minimum 2GB, 8GB+ recommended
- **Disk**: ~500MB for dependencies
- **ffmpeg**: Required for audio/video processing

## Quick Install (Recommended)

For most Linux distributions with Python 3.9+ already installed:

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Restart your shell or run:
source ~/.bashrc  # or ~/.zshrc

# Install ffmpeg (Ubuntu/Debian example)
sudo apt update && sudo apt install -y ffmpeg

# Install mnemofy globally
pipx install mnemofy

# Verify installation
mnemofy version
mnemofy transcribe --list-models
```

## Distribution-Specific Instructions

### Ubuntu/Debian/Mint

**Ubuntu 23.04+ / Debian 12+ (Recommended Method):**

```bash
# Update package list
sudo apt update

# Install Python and ffmpeg
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Install pipx via apt (handles PEP 668 correctly)
sudo apt install -y pipx
pipx ensurepath

# Reload shell configuration
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

**Ubuntu 22.04 and older (Alternative Method):**

```bash
# Update package list
sudo apt update

# Install Python 3.9+ (if not installed)
sudo apt install -y python3 python3-pip python3-venv

# Install ffmpeg
sudo apt install -y ffmpeg

# Install pipx (use apt if available, otherwise pip)
sudo apt install -y pipx || python3 -m pip install --user pipx
pipx ensurepath

# Reload shell configuration
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

**If you encounter "externally-managed-environment" error:**

Modern Debian/Ubuntu systems (23.04+, Debian 12+) implement PEP 668 to prevent breaking system Python packages. Solutions:

```bash
# Option 1: Use system package (RECOMMENDED)
sudo apt install pipx
pipx ensurepath
pipx install mnemofy

# Option 2: Use --break-system-packages (not recommended)
python3 -m pip install --user --break-system-packages pipx
python3 -m pipx ensurepath
pipx install mnemofy

# Option 3: Use virtual environment
python3 -m venv ~/mnemofy-env
~/mnemofy-env/bin/pip install mnemofy
# Then use: ~/mnemofy-env/bin/mnemofy
```

**For Ubuntu 20.04 or older** (Python 3.8 or lower):

```bash
# Add deadsnakes PPA for newer Python
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Use Python 3.12 for pipx
python3.12 -m pip install --user pipx
python3.12 -m pipx ensurepath

# Install mnemofy with Python 3.12
pipx install mnemofy --python python3.12
```

### Fedora/RHEL/CentOS

```bash
# Install Python 3.9+ (Fedora usually includes recent Python)
sudo dnf install -y python3 python3-pip

# Install ffmpeg (requires RPM Fusion repository)
sudo dnf install -y \
  https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm

sudo dnf install -y ffmpeg

# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Reload shell
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

**For RHEL/CentOS 8+**:

```bash
# Enable EPEL and PowerTools
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled powertools

# Install Python 3.9+
sudo dnf install -y python39 python39-pip

# Install ffmpeg from RPM Fusion
sudo dnf install -y \
  https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm

sudo dnf install -y ffmpeg

# Install mnemofy
python3.9 -m pip install --user pipx
python3.9 -m pipx ensurepath
pipx install mnemofy --python python3.9
```

### Arch Linux/Manjaro

```bash
# Install Python and ffmpeg (usually pre-installed)
sudo pacman -Syu python python-pip ffmpeg

# Install pipx
python -m pip install --user pipx
python -m pipx ensurepath

# Reload shell
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

**Using AUR** (if mnemofy is available):

```bash
# Using yay
yay -S mnemofy

# Using paru
paru -S mnemofy
```

### openSUSE

```bash
# Install Python and ffmpeg
sudo zypper install -y python3 python3-pip ffmpeg

# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Reload shell
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

## Installation Methods

### Method 1: pipx (Recommended)

**Best for**: Clean, isolated global CLI tools

```bash
# Install pipx
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install mnemofy
pipx install mnemofy

# Upgrade later
pipx upgrade mnemofy

# Uninstall
pipx uninstall mnemofy
```

**Advantages**:
- ✓ Isolated environment (no conflicts)
- ✓ Easy to upgrade/uninstall
- ✓ Available globally as `mnemofy` command
- ✓ Recommended by Python packaging guide

### Method 2: pip (User Install)

**Best for**: Simple installation without virtual environments

```bash
# Install for current user only (no sudo needed)
python3 -m pip install --user mnemofy

# Add to PATH (if not already)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Upgrade later
python3 -m pip install --user --upgrade mnemofy

# Uninstall
python3 -m pip uninstall mnemofy
```

**Note**: This method may conflict with system packages. Use `pipx` if possible.

### Method 3: From Source

**Best for**: Development, testing, or contributing

```bash
# Install git if needed
sudo apt install git  # Ubuntu/Debian
# sudo dnf install git  # Fedora
# sudo pacman -S git    # Arch

# Clone repository
git clone https://github.com/tiroq/mnemofy.git
cd mnemofy

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"

# Run mnemofy
mnemofy version
```

**For global installation from source**:

```bash
# Clone and navigate to directory
git clone https://github.com/tiroq/mnemofy.git
cd mnemofy

# Install globally using pipx
pipx install .

# Or specify Python version
pipx install . --python python3.12
```

## Verification

After installation, verify mnemofy works correctly:

```bash
# Check version
mnemofy version

# Check model availability
mnemofy transcribe --list-models

# View help
mnemofy --help
mnemofy transcribe --help

# Test with a small audio file
mnemofy transcribe test_audio.mp3
```

**Expected output for `mnemofy version`**:
```
mnemofy version 0.9.3
```

**Expected output for `mnemofy transcribe --list-models`**:
```
                   Available Whisper Models                   
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━┓
┃ Model    ┃ Speed ┃ Quality ┃     RAM ┃ VRAM ┃    Status    ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━┩
│ tiny     │ █████ │  ██░░░  │  1.0 GB │  N/A │ ✓ Compatible │
│ base     │ █████ │  ███░░  │  1.5 GB │  N/A │ ✓ Compatible │
│ small    │ ████░ │  ███░░  │  2.5 GB │  N/A │ ✓ Compatible │
│ medium   │ ███░░ │  ████░  │  5.0 GB │  N/A │ ✓ Compatible │
│ large-v3 │ ██░░░ │  █████  │ 10.0 GB │  N/A │   ⚠ Risky    │
└──────────┴───────┴─────────┴─────────┴──────┴──────────────┘
```

## Troubleshooting

### "externally-managed-environment" Error (PEP 668)

If you see this error when trying to install pipx:

```
error: externally-managed-environment
× This environment is externally managed
```

This is a security feature in modern Debian/Ubuntu systems (23.04+, Debian 12+) to protect system Python packages.

**Solution 1: Use system package manager (RECOMMENDED):**

```bash
# Install pipx from apt
sudo apt install pipx
pipx ensurepath
source ~/.bashrc

# Install mnemofy
pipx install mnemofy
```

**Solution 2: Use virtual environment:**

```bash
# Create a dedicated virtual environment for mnemofy
python3 -m venv ~/.mnemofy-venv
source ~/.mnemofy-venv/bin/activate
pip install mnemofy

# Add alias to bashrc for easy access
echo 'alias mnemofy="$HOME/.mnemofy-venv/bin/mnemofy"' >> ~/.bashrc
source ~/.bashrc
```

**Solution 3: Override protection (NOT RECOMMENDED):**

```bash
# Only use if you understand the risks
python3 -m pip install --user --break-system-packages pipx
python3 -m pipx ensurepath
pipx install mnemofy
```

### Command Not Found

If `mnemofy` command is not found after installation:

```bash
# Check if ~/.local/bin is in PATH
echo $PATH | grep -q "$HOME/.local/bin" && echo "✓ In PATH" || echo "✗ Not in PATH"

# Add to PATH permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or for zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Python Version Too Old

```bash
# Check current Python version
python3 --version

# If < 3.9, install newer version:

# Ubuntu/Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv

# Fedora/RHEL
sudo dnf install python3.12

# Then use specific version
pipx install mnemofy --python python3.12
```

### FFmpeg Not Found

```bash
# Check if ffmpeg is installed
which ffmpeg

# If not found, install:

# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora/RHEL (requires RPM Fusion)
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg

# Verify
ffmpeg -version
```

### Permission Denied Errors

If you get permission errors during installation:

```bash
# Never use sudo with pip install!
# Instead, use --user flag:
python3 -m pip install --user mnemofy

# Or use pipx (recommended)
pipx install mnemofy
```

### Module Import Errors

If you see `ModuleNotFoundError` errors:

```bash
# Reinstall in clean environment
pipx uninstall mnemofy
pipx install mnemofy --python python3.12

# Or from source
cd mnemofy
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### GPU/CUDA Issues

If you have NVIDIA GPU but it's not detected:

```bash
# Check CUDA availability
nvidia-smi

# If CUDA is not installed, either:
# 1. Use CPU-only mode
mnemofy transcribe file.mp4 --no-gpu

# 2. Install CUDA toolkit (Ubuntu/Debian example)
sudo apt install nvidia-cuda-toolkit

# Verify
nvidia-smi
```

### Slow First Run

The first time you run mnemofy, it downloads the Whisper model which may take a few minutes:

```bash
# Models are cached in ~/.cache/huggingface/
# Tiny model: ~75 MB
# Base model: ~145 MB
# Small model: ~466 MB
# Medium model: ~1.5 GB
# Large-v3 model: ~3.1 GB
```

### Out of Memory Errors

If transcription fails with OOM errors:

```bash
# Use a smaller model
mnemofy transcribe file.mp4 --model tiny

# Or force CPU mode
mnemofy transcribe file.mp4 --no-gpu

# Check available RAM
free -h
```

## Server/Headless Installation

For servers without display (SSH, Docker, CI/CD):

```bash
# Install dependencies
sudo apt install -y python3 python3-pip ffmpeg

# Install mnemofy
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install mnemofy

# Use headless mode
mnemofy transcribe meeting.mp4 --auto

# Or specify model explicitly
mnemofy transcribe meeting.mp4 --model base
```

## Docker Installation

If you prefer containerized installation:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install mnemofy
RUN pip install mnemofy

# Set working directory
WORKDIR /workspace

# Default command
ENTRYPOINT ["mnemofy"]
CMD ["--help"]
```

Build and run:

```bash
# Build image
docker build -t mnemofy .

# Run mnemofy
docker run -v $(pwd):/workspace mnemofy transcribe meeting.mp4
```

## Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Issue Tracker**: https://github.com/tiroq/mnemofy/issues
- **PyPI Package**: https://pypi.org/project/mnemofy/
- **Homepage**: https://github.com/tiroq/mnemofy

## Need Help?

If you encounter issues not covered here:

1. Check existing issues: https://github.com/tiroq/mnemofy/issues
2. Create a new issue with:
   - Your Linux distribution and version
   - Python version (`python3 --version`)
   - Installation method used
   - Complete error message
   - Steps to reproduce

---

**Last updated**: February 2026  
**mnemofy version**: 0.9.3
