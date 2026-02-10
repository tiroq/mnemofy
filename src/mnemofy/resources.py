"""
System resource detection for adaptive ASR model selection.

This module provides cross-platform detection of CPU, RAM, and GPU resources
to determine which Whisper model best fits the available hardware.

Classes:
    SystemResources: Dataclass representing detected system capabilities.

Functions:
    detect_system_resources: Main entry point for resource detection.
    get_cpu_info: Detect CPU cores and architecture.
    get_memory_info: Detect total and available RAM.
    get_gpu_info: Detect GPU availability and VRAM.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemResources:
    """Detected system hardware capabilities.
    
    Attributes:
        cpu_cores (int): Number of logical CPU cores.
        cpu_arch (str): CPU architecture (e.g., 'arm64', 'x86_64').
        total_ram_gb (float): Total system RAM in GB.
        available_ram_gb (float): Available system RAM in GB.
        has_gpu (bool): Whether a GPU is detected.
        gpu_type (Optional[str]): Type of GPU if detected ('cuda', 'metal', 'rocm', or None).
        available_vram_gb (Optional[float]): Available GPU VRAM in GB (None if not detected).
    """

    cpu_cores: int
    cpu_arch: str
    total_ram_gb: float
    available_ram_gb: float
    has_gpu: bool
    gpu_type: Optional[str]
    available_vram_gb: Optional[float]

    def __str__(self) -> str:
        """Return human-readable summary of system resources."""
        if self.has_gpu:
            if self.available_vram_gb is not None:
                gpu_info = f" | GPU: {self.gpu_type} ({self.available_vram_gb:.1f}GB)"
            else:
                # Metal GPU with unified memory
                gpu_info = f" | GPU: {self.gpu_type} (unified memory)"
        else:
            gpu_info = ""
        return (
            f"CPU: {self.cpu_cores} cores ({self.cpu_arch}) | "
            f"RAM: {self.available_ram_gb:.1f}GB/{self.total_ram_gb:.1f}GB{gpu_info}"
        )


def get_cpu_info() -> Tuple[int, str]:
    """Detect CPU cores and architecture.
    
    Returns:
        Tuple[int, str]: (number of logical cores, architecture string).
    
    Notes:
        This function never raises on detection failure. If CPU detection fails for any
        reason, a warning is logged and fallback values ``(1, "unknown")`` are returned.
    """
    try:
        cores = psutil.cpu_count(logical=True) or 1
        arch = platform.machine()
        logger.debug(f"Detected CPU: {cores} cores, {arch}")
        return cores, arch
    except Exception as e:
        logger.warning(f"CPU detection failed: {e}. Using fallback values (1 core, unknown arch).")
        return 1, "unknown"


def get_memory_info() -> Tuple[float, float]:
    """Detect total and available system RAM.
    
    Returns:
        Tuple[float, float]: (total RAM in GB, available RAM in GB)
        
    Note:
        Values are rounded to 2 decimal places.
    """
    try:
        memory = psutil.virtual_memory()
        total_gb = round(memory.total / (1024 ** 3), 2)
        available_gb = round(memory.available / (1024 ** 3), 2)
        
        # Sanity check: available should not exceed total
        if available_gb > total_gb:
            logger.warning(f"Available RAM ({available_gb}GB) exceeds total ({total_gb}GB). "
                           "Capping available to total.")
            available_gb = total_gb
        
        logger.debug(f"Detected RAM: {available_gb}GB available / {total_gb}GB total")
        return total_gb, available_gb
    except Exception as e:
        logger.warning(f"Memory detection failed: {e}. Using fallback values (0GB).")
        return 0.0, 0.0


def _detect_cuda() -> bool:
    """Check if CUDA (NVIDIA) is available via nvidia-smi."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def _get_cuda_vram() -> Optional[float]:
    """Query NVIDIA GPU VRAM via nvidia-smi.
    
    Returns:
        Optional[float]: VRAM in GB, or None if detection fails.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            # nvidia-smi returns memory in MB
            vram_mb = int(result.stdout.strip().split('\n')[0])
            vram_gb = round(vram_mb / 1024, 2)
            logger.debug(f"Detected CUDA VRAM: {vram_gb}GB")
            return vram_gb
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired, Exception) as e:
        logger.debug(f"CUDA VRAM detection via nvidia-smi failed: {e}")
    return None


def _detect_metal() -> bool:
    """Check if Metal (Apple Silicon) is available.
    
    Metal is available on:
    - macOS with Apple Silicon (ARM64 architecture)
    """
    try:
        is_darwin = platform.system() == "Darwin"
        is_arm = platform.machine() in ("arm64", "aarch64")
        
        if is_darwin and is_arm:
            logger.debug("Detected Metal GPU (Apple Silicon)")
            return True
        return False
    except Exception as e:
        logger.warning(f"Metal detection failed: {e}")
        return False


def _detect_rocm() -> bool:
    """Check if ROCm (AMD) is available via rocm-smi.
    
    Note: Low priority support. Primarily Linux-only.
    """
    try:
        result = subprocess.run(
            ["rocm-smi", "--version"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def get_gpu_info() -> Tuple[bool, Optional[str], Optional[float]]:
    """Detect GPU availability, type, and VRAM.
    
    Checks in order:
    1. CUDA (NVIDIA)
    2. Metal (Apple Silicon)
    3. ROCm (AMD) - not implemented yet
    
    Returns:
        Tuple[bool, Optional[str], Optional[float]]: 
            (gpu_available, gpu_type, vram_gb)
            
    Note:
        - For Metal, vram_gb is None (uses unified memory, reported as available_ram)
        - For ROCm, vram_gb is not implemented yet
        - On detection failure, gracefully returns (False, None, None)
    """
    try:
        # Check CUDA first
        if _detect_cuda():
            vram = _get_cuda_vram()
            logger.debug(f"Using CUDA GPU with {vram}GB VRAM" if vram else "CUDA GPU detected")
            return True, "cuda", vram
        
        # Check Metal
        if _detect_metal():
            logger.debug("Using Metal GPU (integrated, unified memory)")
            return True, "metal", None
        
        # TODO: Add ROCm (AMD GPU) detection and VRAM reporting in a future release.
        
        # No GPU detected
        logger.debug("No GPU detected, using CPU mode")
        return False, None, None
        
    except Exception as e:
        logger.warning(f"GPU detection failed: {e}. Falling back to CPU mode.")
        return False, None, None


def detect_system_resources(no_gpu: bool = False) -> SystemResources:
    """Detect all system resources.
    
    Main entry point for resource detection. Orchestrates CPU, memory, and GPU detection
    with graceful error handling.
    
    Args:
        no_gpu (bool): If True, skip GPU detection (force CPU-only mode).
        
    Returns:
        SystemResources: Detected system capabilities.
        
    Note:
        Partial detection failures are handled gracefully:
        - CPU detection failure → defaults to 1 core, 'unknown' arch
        - Memory detection failure → defaults to 0GB
        - GPU detection failure → assumes no GPU available
    """
    # Detect CPU with individual error handling
    try:
        cpu_cores, cpu_arch = get_cpu_info()
    except Exception as e:
        logger.warning(f"CPU detection failed: {e}")
        cpu_cores, cpu_arch = 1, "unknown"
    
    # Detect RAM with individual error handling
    try:
        total_ram_gb, available_ram_gb = get_memory_info()
    except Exception as e:
        logger.warning(f"Memory detection failed: {e}")
        total_ram_gb, available_ram_gb = 0.0, 0.0
    
    # Detect GPU (if not disabled) with individual error handling
    if no_gpu:
        has_gpu, gpu_type, vram = False, None, None
        logger.info("GPU detection disabled via --no-gpu")
    else:
        try:
            has_gpu, gpu_type, vram = get_gpu_info()
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
            has_gpu, gpu_type, vram = False, None, None
    
    resources = SystemResources(
        cpu_cores=cpu_cores,
        cpu_arch=cpu_arch,
        total_ram_gb=total_ram_gb,
        available_ram_gb=available_ram_gb,
        has_gpu=has_gpu,
        gpu_type=gpu_type,
        available_vram_gb=vram
    )
    
    logger.info(f"Detected resources: {resources}")
    return resources
