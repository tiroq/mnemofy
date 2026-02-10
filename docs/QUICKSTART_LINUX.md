# Linux Quick Start Guide

One-page reference for installing and using mnemofy on Linux.

## One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/tiroq/mnemofy/main/scripts/install.sh | bash
```

Or using wget:

```bash
wget -qO- https://raw.githubusercontent.com/tiroq/mnemofy/main/scripts/install.sh | bash
```

## Manual Installation (3 Steps)

### 1. Install Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y python3 python3-pip ffmpeg
```

**Fedora:**
```bash
sudo dnf install -y python3 python3-pip
sudo dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
sudo dnf install -y ffmpeg
```

**Arch:**
```bash
sudo pacman -Syu python python-pip ffmpeg
```

### 2. Install pipx

**Modern systems (Ubuntu 23.04+, Debian 12+):**
```bash
sudo apt install pipx
pipx ensurepath
source ~/.bashrc  # or ~/.zshrc
```

**Older systems:**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
source ~/.bashrc  # or ~/.zshrc
```

> **Note:** If you see "externally-managed-environment" error, see [INSTALL_LINUX.md](../INSTALL_LINUX.md#externally-managed-environment-error-pep-668) for solutions.

### 3. Install mnemofy

```bash
pipx install mnemofy
```

## First Use

```bash
# Check installation
mnemofy version

# View available models
mnemofy transcribe --list-models

# Transcribe a file
mnemofy transcribe meeting.mp4
```

## Common Commands

```bash
# Basic transcription
mnemofy transcribe audio.mp3

# Specify output directory
mnemofy transcribe video.mkv --outdir output/

# Use specific model
mnemofy transcribe file.mp4 --model small

# Different language
mnemofy transcribe french.mp4 --lang fr

# Headless/automated mode
mnemofy transcribe file.mp4 --auto

# CPU-only mode
mnemofy transcribe file.mp4 --no-gpu
```

## Troubleshooting

### Command not found
```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

### Python too old
```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12
pipx install mnemofy --python python3.12
```

### FFmpeg missing
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora (requires RPM Fusion)
sudo dnf install ffmpeg
```

## Files & Locations

- **Config**: `~/.config/mnemofy/`
- **Cache**: `~/.cache/huggingface/`
- **Models**: `~/.cache/huggingface/hub/`
- **Binary**: `~/.local/bin/mnemofy` (via pipx)

## Output Files

For input `meeting.mp4`, mnemofy creates:

- `meeting.transcript.txt` - Timestamped text
- `meeting.transcript.srt` - Subtitles
- `meeting.transcript.json` - Structured data
- `meeting.notes.md` - Meeting notes

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9 | 3.12+ |
| RAM | 2 GB | 8 GB+ |
| Disk | 500 MB | 2 GB |
| ffmpeg | Any | Latest |

## Model Selection

| Model | RAM | Speed | Quality | Use Case |
|-------|-----|-------|---------|----------|
| tiny | 1.0 GB | ★★★★★ | ★★☆☆☆ | Testing, low-end systems |
| base | 1.5 GB | ★★★★★ | ★★★☆☆ | General use |
| small | 2.5 GB | ★★★★☆ | ★★★☆☆ | Good balance |
| medium | 5.0 GB | ★★★☆☆ | ★★★★☆ | High accuracy |
| large-v3 | 10.0 GB | ★★☆☆☆ | ★★★★★ | Best quality |

## Distribution-Specific

### Ubuntu 20.04 (Python 3.8)
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip ffmpeg
pipx install mnemofy --python python3.12
```

### CentOS/RHEL 8
```bash
sudo dnf install epel-release
sudo dnf config-manager --set-enabled powertools
sudo dnf install python39 python39-pip
sudo dnf install https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
sudo dnf install ffmpeg
python3.9 -m pip install --user pipx
pipx install mnemofy --python python3.9
```

### Arch/Manjaro
```bash
sudo pacman -Syu python python-pip ffmpeg
python -m pip install --user pipx
python -m pipx ensurepath
pipx install mnemofy
```

## Docker One-Liner

```bash
docker run -v $(pwd):/workspace --rm \
  python:3.12-slim sh -c \
  "apt-get update && apt-get install -y ffmpeg && \
   pip install mnemofy && \
   mnemofy transcribe /workspace/yourfile.mp4"
```

## Getting Help

- **Full guide**: [INSTALL_LINUX.md](INSTALL_LINUX.md)
- **Issues**: https://github.com/tiroq/mnemofy/issues
- **Docs**: https://github.com/tiroq/mnemofy

---

**Quick reference version 1.0** | Updated Feb 2026
