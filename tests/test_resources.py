"""
Tests for resource detection module.

Tests cover:
- CPU detection (cores, architecture)
- Memory detection (total, available)
- GPU detection (CUDA, Metal, fallback)
- Error handling and graceful degradation
"""

import platform
from unittest.mock import MagicMock, patch, Mock

import pytest

from mnemofy.resources import (
    SystemResources,
    detect_system_resources,
    get_cpu_info,
    get_memory_info,
    get_gpu_info,
    _detect_cuda,
    _get_cuda_vram,
    _detect_metal,
)


class TestSystemResources:
    """Test SystemResources dataclass."""

    def test_construction(self):
        """Test creating SystemResources instance."""
        resources = SystemResources(
            cpu_cores=8,
            cpu_arch="x86_64",
            total_ram_gb=16.0,
            available_ram_gb=12.5,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=6.0
        )
        assert resources.cpu_cores == 8
        assert resources.gpu_type == "cuda"

    def test_string_representation(self):
        """Test __str__ method."""
        resources = SystemResources(
            cpu_cores=4,
            cpu_arch="arm64",
            total_ram_gb=8.0,
            available_ram_gb=6.0,
            has_gpu=True,
            gpu_type="metal",
            available_vram_gb=None
        )
        result = str(resources)
        assert "4 cores" in result
        assert "6.0GB" in result
        assert "metal" in result

    def test_string_representation_no_gpu(self):
        """Test __str__ with no GPU."""
        resources = SystemResources(
            cpu_cores=2,
            cpu_arch="unknown",
            total_ram_gb=2.0,
            available_ram_gb=1.5,
            has_gpu=False,
            gpu_type=None,
            available_vram_gb=None
        )
        result = str(resources)
        assert "GPU" not in result
        assert "1.5GB" in result


class TestCPUDetection:
    """Test CPU detection."""

    @patch("mnemofy.resources.psutil.cpu_count")
    @patch("mnemofy.resources.platform.machine")
    def test_cpu_detection_success(self, mock_machine, mock_cpu_count):
        """Test successful CPU detection."""
        mock_cpu_count.return_value = 8
        mock_machine.return_value = "x86_64"
        
        cores, arch = get_cpu_info()
        
        assert cores == 8
        assert arch == "x86_64"
        mock_cpu_count.assert_called_once_with(logical=True)

    @patch("mnemofy.resources.psutil.cpu_count")
    @patch("mnemofy.resources.platform.machine")
    def test_cpu_detection_fallback_on_none(self, mock_machine, mock_cpu_count):
        """Test CPU detection fallback when psutil returns None."""
        mock_cpu_count.return_value = None
        mock_machine.return_value = "arm64"
        
        cores, arch = get_cpu_info()
        
        # Should default to 1 core when psutil returns None
        assert cores == 1
        assert arch == "arm64"

    @patch("mnemofy.resources.psutil.cpu_count")
    def test_cpu_detection_failure(self, mock_cpu_count):
        """Test CPU detection graceful failure."""
        mock_cpu_count.side_effect = Exception("psutil error")
        
        cores, arch = get_cpu_info()
        
        # Should fall back to defaults
        assert cores == 1
        assert arch == "unknown"


class TestMemoryDetection:
    """Test memory detection."""

    @patch("mnemofy.resources.psutil.virtual_memory")
    def test_memory_detection_success(self, mock_memory):
        """Test successful memory detection."""
        mock_vm = MagicMock()
        mock_vm.total = 16 * (1024 ** 3)  # 16GB
        mock_vm.available = 12.5 * (1024 ** 3)  # 12.5GB
        mock_memory.return_value = mock_vm
        
        total, available = get_memory_info()
        
        assert total == 16.0
        assert available == 12.5

    @patch("mnemofy.resources.psutil.virtual_memory")
    def test_memory_detection_available_exceeds_total(self, mock_memory):
        """Test graceful handling when available > total (edge case)."""
        mock_vm = MagicMock()
        mock_vm.total = 2 * (1024 ** 3)  # 2GB
        mock_vm.available = 3 * (1024 ** 3)  # 3GB (shouldn't happen)
        mock_memory.return_value = mock_vm
        
        total, available = get_memory_info()
        
        # Should cap available to total
        assert available <= total

    @patch("mnemofy.resources.psutil.virtual_memory")
    def test_memory_detection_failure(self, mock_memory):
        """Test memory detection graceful failure."""
        mock_memory.side_effect = Exception("psutil error")
        
        total, available = get_memory_info()
        
        # Should fall back to 0GB
        assert total == 0.0
        assert available == 0.0


class TestGPUDetection:
    """Test GPU detection."""

    @patch("mnemofy.resources._detect_metal")
    @patch("mnemofy.resources._detect_cuda")
    def test_cuda_detection_priority(self, mock_cuda, mock_metal):
        """Test that CUDA is checked before Metal."""
        mock_cuda.return_value = True
        mock_metal.return_value = True
        
        has_gpu, gpu_type, vram = get_gpu_info()
        
        assert has_gpu is True
        assert gpu_type == "cuda"
        # CUDA should be checked first
        mock_cuda.assert_called_once()


    @patch("mnemofy.resources._detect_metal")
    @patch("mnemofy.resources._detect_cuda")
    def test_metal_detection_fallback(self, mock_cuda, mock_metal):
        """Test Metal detection when CUDA not available."""
        mock_cuda.return_value = False
        mock_metal.return_value = True
        
        has_gpu, gpu_type, vram = get_gpu_info()
        
        assert has_gpu is True
        assert gpu_type == "metal"
        assert vram is None  # Metal doesn't report VRAM

    @patch("mnemofy.resources._detect_metal")
    @patch("mnemofy.resources._detect_cuda")
    def test_no_gpu_detected(self, mock_cuda, mock_metal):
        """Test when no GPU is detected."""
        mock_cuda.return_value = False
        mock_metal.return_value = False
        
        has_gpu, gpu_type, vram = get_gpu_info()
        
        assert has_gpu is False
        assert gpu_type is None
        assert vram is None


class TestCUDADetection:
    """Test CUDA-specific detection."""

    @patch("mnemofy.resources.subprocess.run")
    def test_cuda_detection_success(self, mock_run):
        """Test successful CUDA detection via nvidia-smi."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NVIDIA GeForce RTX 3080"
        mock_run.return_value = mock_result
        
        result = _detect_cuda()
        
        assert result is True
        mock_run.assert_called_once()

    @patch("mnemofy.resources.subprocess.run")
    def test_cuda_detection_failure_no_nvidia_smi(self, mock_run):
        """Test CUDA detection when nvidia-smi not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = _detect_cuda()
        
        assert result is False

    @patch("mnemofy.resources.subprocess.run")
    def test_cuda_detection_failure_timeout(self, mock_run):
        """Test CUDA detection when nvidia-smi times out."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("nvidia-smi", timeout=2)
        
        result = _detect_cuda()
        
        assert result is False

    @patch("mnemofy.resources.subprocess.run")
    def test_cuda_vram_detection_success(self, mock_run):
        """Test successful VRAM detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "10240"  # 10GB in MB
        mock_run.return_value = mock_result
        
        vram = _get_cuda_vram()
        
        assert vram == 10.0

    @patch("mnemofy.resources.subprocess.run")
    def test_cuda_vram_detection_failure(self, mock_run):
        """Test CUDA VRAM detection failure."""
        mock_run.side_effect = FileNotFoundError()
        
        vram = _get_cuda_vram()
        
        assert vram is None


class TestMetalDetection:
    """Test Metal-specific detection."""

    @patch("mnemofy.resources.platform.machine")
    @patch("mnemofy.resources.platform.system")
    def test_metal_detection_apple_silicon(self, mock_system, mock_machine):
        """Test Metal detection on Apple Silicon."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "arm64"
        
        result = _detect_metal()
        
        assert result is True

    @patch("mnemofy.resources.platform.machine")
    @patch("mnemofy.resources.platform.system")
    def test_metal_detection_intel_mac(self, mock_system, mock_machine):
        """Test Metal detection on Intel Mac (should be False)."""
        mock_system.return_value = "Darwin"
        mock_machine.return_value = "x86_64"
        
        result = _detect_metal()
        
        assert result is False

    @patch("mnemofy.resources.platform.machine")
    @patch("mnemofy.resources.platform.system")
    def test_metal_detection_non_mac(self, mock_system, mock_machine):
        """Test Metal detection on non-Mac system."""
        mock_system.return_value = "Linux"
        mock_machine.return_value = "arm64"
        
        result = _detect_metal()
        
        assert result is False


class TestDetectSystemResources:
    """Test main orchestration function."""

    @patch("mnemofy.resources.get_gpu_info")
    @patch("mnemofy.resources.get_memory_info")
    @patch("mnemofy.resources.get_cpu_info")
    def test_full_detection_success(self, mock_cpu, mock_mem, mock_gpu):
        """Test successful full resource detection."""
        mock_cpu.return_value = (8, "x86_64")
        mock_mem.return_value = (16.0, 12.0)
        mock_gpu.return_value = (True, "cuda", 8.0)
        
        resources = detect_system_resources()
        
        assert resources.cpu_cores == 8
        assert resources.available_ram_gb == 12.0
        assert resources.has_gpu is True
        assert resources.gpu_type == "cuda"

    @patch("mnemofy.resources.get_gpu_info")
    @patch("mnemofy.resources.get_memory_info")
    @patch("mnemofy.resources.get_cpu_info")
    def test_no_gpu_flag(self, mock_cpu, mock_mem, mock_gpu):
        """Test that --no-gpu disables GPU detection."""
        mock_cpu.return_value = (8, "x86_64")
        mock_mem.return_value = (16.0, 12.0)
        
        resources = detect_system_resources(no_gpu=True)
        
        assert resources.has_gpu is False
        assert resources.gpu_type is None
        # GPU detection function should not be called
        mock_gpu.assert_not_called()

    @patch("mnemofy.resources.get_gpu_info")
    @patch("mnemofy.resources.get_memory_info")
    @patch("mnemofy.resources.get_cpu_info")
    def test_partial_failure_cpu(self, mock_cpu, mock_mem, mock_gpu):
        """Test graceful handling of CPU detection failure."""
        mock_cpu.side_effect = Exception("CPU error")
        mock_mem.return_value = (16.0, 12.0)
        mock_gpu.return_value = (False, None, None)
        
        resources = detect_system_resources()
        
        # Should have fallback CPU values
        assert resources.cpu_cores >= 1
        # Other values should be set
        assert resources.available_ram_gb == 12.0

    @patch("mnemofy.resources.get_gpu_info")
    @patch("mnemofy.resources.get_memory_info")
    @patch("mnemofy.resources.get_cpu_info")
    def test_catastrophic_failure(self, mock_cpu, mock_mem, mock_gpu):
        """Test fallback on catastrophic failure."""
        mock_cpu.side_effect = Exception("CPU error")
        mock_mem.side_effect = Exception("Memory error")
        mock_gpu.side_effect = Exception("GPU error")
        
        resources = detect_system_resources()
        
        # Should have conservative defaults
        assert resources.cpu_cores == 1
        assert resources.available_ram_gb == 0.0
        assert resources.has_gpu is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
