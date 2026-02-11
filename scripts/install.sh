#!/bin/bash
# Quick Linux Installation Script for mnemofy
# Supports Ubuntu/Debian, Fedora/RHEL, and Arch Linux
#
# Usage: curl -sSL https://raw.githubusercontent.com/tiroq/mnemofy/main/scripts/install.sh | bash
# Or: wget -qO- https://raw.githubusercontent.com/tiroq/mnemofy/main/scripts/install.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "Cannot detect OS. /etc/os-release not found."
        exit 1
    fi
    
    log_info "Detected OS: $OS $OS_VERSION"
}

# Check Python version
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if version is >= 3.9
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            log_success "Python 3.9+ detected"
            return 0
        else
            log_warning "Python version is less than 3.9"
            return 1
        fi
    else
        log_warning "Python 3 not found"
        return 1
    fi
}

# Install Python 3.9+ on Ubuntu/Debian
install_python_debian() {
    log_info "Installing Python 3.12 on Ubuntu/Debian..."
    
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
    
    log_success "Python 3.12 installed"
}

# Install Python on Fedora/RHEL
install_python_fedora() {
    log_info "Installing Python 3 on Fedora/RHEL..."
    sudo dnf install -y python3 python3-pip
    log_success "Python installed"
}

# Install Python on Arch
install_python_arch() {
    log_info "Installing Python on Arch Linux..."
    sudo pacman -Syu --noconfirm python python-pip
    log_success "Python installed"
}

# Install ffmpeg
install_ffmpeg() {
    log_info "Installing ffmpeg..."
    
    case "$OS" in
        ubuntu|debian|linuxmint|pop)
            sudo apt update
            sudo apt install -y ffmpeg
            ;;
        fedora)
            # Install RPM Fusion
            sudo dnf install -y \
                https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
            sudo dnf install -y ffmpeg
            ;;
        rhel|centos|rocky|almalinux)
            # Install EPEL and RPM Fusion
            sudo dnf install -y epel-release
            sudo dnf install -y \
                https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
            sudo dnf install -y ffmpeg
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm ffmpeg
            ;;
        opensuse|opensuse-leap|opensuse-tumbleweed)
            sudo zypper install -y ffmpeg
            ;;
        *)
            log_error "Unsupported OS for automatic ffmpeg installation: $OS"
            log_info "Please install ffmpeg manually and re-run this script"
            exit 1
            ;;
    esac
    
    log_success "ffmpeg installed"
}

# Install pipx
install_pipx() {
    log_info "Installing pipx..."
    
    # Try using system package manager first (preferred on modern Debian/Ubuntu)
    case "$OS" in
        ubuntu|debian|linuxmint|pop)
            # Ubuntu 23.04+, Debian 12+ use PEP 668 externally managed environments
            if sudo apt install -y pipx 2>/dev/null; then
                log_success "pipx installed via apt"
                pipx ensurepath
                export PATH="$HOME/.local/bin:$PATH"
                return 0
            fi
            ;;
        fedora|rhel|centos|rocky|almalinux)
            if sudo dnf install -y pipx 2>/dev/null; then
                log_success "pipx installed via dnf"
                pipx ensurepath
                export PATH="$HOME/.local/bin:$PATH"
                return 0
            fi
            ;;
        arch|manjaro)
            if sudo pacman -S --noconfirm python-pipx 2>/dev/null; then
                log_success "pipx installed via pacman"
                pipx ensurepath
                export PATH="$HOME/.local/bin:$PATH"
                return 0
            fi
            ;;
    esac
    
    # Fallback to pip install (for older systems)
    log_info "System package not available, trying pip install..."
    
    if command -v python3.12 &> /dev/null; then
        if python3.12 -m pip install --user pipx 2>/dev/null; then
            python3.12 -m pipx ensurepath
        else
            # Handle PEP 668 externally-managed-environment
            log_warning "PEP 668 restriction detected, using --break-system-packages"
            python3.12 -m pip install --user --break-system-packages pipx
            python3.12 -m pipx ensurepath
        fi
    else
        if python3 -m pip install --user pipx 2>/dev/null; then
            python3 -m pipx ensurepath
        else
            # Handle PEP 668 externally-managed-environment
            log_warning "PEP 668 restriction detected, using --break-system-packages"
            python3 -m pip install --user --break-system-packages pipx
            python3 -m pipx ensurepath
        fi
    fi
    
    # Add to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"
    
    log_success "pipx installed"
}

# Install mnemofy
install_mnemofy() {
    log_info "Installing mnemofy..."
    
    if command -v python3.12 &> /dev/null; then
        pipx install mnemofy --python python3.12
    else
        pipx install mnemofy
    fi
    
    log_success "mnemofy installed"
}

# Upgrade mnemofy
upgrade_mnemofy() {
    log_info "Upgrading mnemofy..."
    
    if pipx upgrade mnemofy; then
        log_success "mnemofy upgraded successfully"
        return 0
    else
        log_error "Failed to upgrade mnemofy"
        return 1
    fi
}

# Check if mnemofy is already installed
is_mnemofy_installed() {
    command -v mnemofy &> /dev/null
}

# Show upgrade prompt
prompt_upgrade() {
    echo ""
    log_info "mnemofy is already installed"
    
    # Get current and latest versions
    CURRENT_VERSION=$(mnemofy version 2>&1 | grep -o '[0-9]*\.[0-9]*\.[0-9]*' || echo "unknown")
    log_info "Current version: $CURRENT_VERSION"
    
    echo ""
    read -p "Do you want to upgrade mnemofy? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    if command -v mnemofy &> /dev/null; then
        VERSION=$(mnemofy version 2>&1 | grep -o '[0-9]*\.[0-9]*\.[0-9]*' || echo "unknown")
        log_success "mnemofy $VERSION is installed and ready to use!"
        
        echo ""
        log_info "Try it out:"
        echo "  mnemofy --help"
        echo "  mnemofy transcribe --list-models"
        echo "  mnemofy transcribe your_file.mp4"
        echo ""
    else
        log_warning "mnemofy command not found in PATH"
        log_info "You may need to restart your shell or run:"
        echo "  source ~/.bashrc  # or ~/.zshrc"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# Main installation flow
main() {
    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   mnemofy Linux Installation Script  ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    
    # Check if mnemofy is already installed
    if is_mnemofy_installed; then
        if prompt_upgrade; then
            # Upgrade mode
            log_info "Starting upgrade..."
            upgrade_mnemofy
            verify_installation
            echo ""
            log_success "Upgrade complete!"
            echo ""
            return 0
        else
            log_info "Skipping upgrade. mnemofy is still installed."
            verify_installation
            return 0
        fi
    fi
    
    # Fresh installation flow
    detect_os
    
    # Check/install Python
    if ! check_python; then
        case "$OS" in
            ubuntu|debian|linuxmint|pop)
                install_python_debian
                ;;
            fedora|rhel|centos|rocky|almalinux)
                install_python_fedora
                ;;
            arch|manjaro)
                install_python_arch
                ;;
            *)
                log_error "Unsupported OS: $OS"
                log_info "Please install Python 3.9+ manually"
                exit 1
                ;;
        esac
    fi
    
    # Check/install ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        install_ffmpeg
    else
        log_success "ffmpeg is already installed"
    fi
    
    # Install pipx
    if ! command -v pipx &> /dev/null; then
        install_pipx
    else
        log_success "pipx is already installed"
    fi
    
    # Install mnemofy
    install_mnemofy
    
    # Verify installation
    verify_installation
    
    echo ""
    log_success "Installation complete!"
    echo ""
    log_info "For detailed documentation, visit:"
    echo "  https://github.com/tiroq/mnemofy/blob/main/INSTALL_LINUX.md"
    echo ""
}

# Run main function
main
