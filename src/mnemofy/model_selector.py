"""Model selection logic for adaptive ASR model choice based on system resources.

This module provides:
- ModelSpec: Data model describing Whisper model capabilities and requirements
- MODEL_SPECS: Database of available models with memory requirements and ratings
- filter_compatible_models: Filter models based on available system resources
- recommend_model: Select best model with reasoning explanation
- get_model_table: Generate formatted table of models with compatibility status
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from rich.table import Table

if TYPE_CHECKING:
    from mnemofy.resources import SystemResources

logger = logging.getLogger(__name__)


class ModelSelectionError(Exception):
    """Raised when no compatible models can be found for available resources."""

    pass


@dataclass(frozen=True)
class ModelSpec:
    """Specification for a Whisper ASR model.
    
    Attributes:
        name: Model identifier (e.g., 'tiny', 'base', 'small', 'medium', 'large-v3')
        min_ram_gb: Minimum RAM required for CPU-only inference (float, GB)
        min_vram_gb: Minimum VRAM required for GPU inference (float, GB).
                    None for models that don't support GPU or use unified memory.
        speed_rating: Relative transcription speed (1=slowest, 5=fastest/real-time)
        quality_rating: Relative accuracy/quality (1=lowest quality / highest WER,
                       5=highest quality / lowest WER). Based on Word Error Rate (WER)
                       benchmark performance.
        description: Human-readable description of model characteristics and use cases
    
    Notes:
        - RAM/VRAM values are conservative estimates including weights + inference overhead
        - Speed rating reflects relative performance; actual speed depends on hardware
        - Quality rating reflects general accuracy; specific WER varies by audio domain
    """
    name: str
    min_ram_gb: float
    min_vram_gb: Optional[float]
    speed_rating: int  # 1-5 scale
    quality_rating: int  # 1-5 scale
    description: str

    def __post_init__(self) -> None:
        """Validate rating scales."""
        if not 1 <= self.speed_rating <= 5:
            raise ValueError(f"speed_rating must be 1-5, got {self.speed_rating}")
        if not 1 <= self.quality_rating <= 5:
            raise ValueError(f"quality_rating must be 1-5, got {self.quality_rating}")


# Database of available Whisper models with memory requirements and ratings
# Based on faster-whisper documentation and empirical testing
# Memory requirements include model weights + inference overhead (conservative estimates)
# VRAM lower than RAM due to int8 quantization optimization in CTranslate2
MODEL_SPECS: Dict[str, ModelSpec] = {
    "tiny": ModelSpec(
        name="tiny",
        min_ram_gb=1.0,
        min_vram_gb=1.0,
        speed_rating=5,  # Fastest
        quality_rating=2,  # Basic accuracy
        description=(
            "Smallest model (39M parameters). Best for fast transcription on limited hardware. "
            "Reasonable accuracy for clear audio. Ideal for real-time or resource-constrained systems."
        ),
    ),
    "base": ModelSpec(
        name="base",
        min_ram_gb=1.5,
        min_vram_gb=1.5,
        speed_rating=5,  # Very fast
        quality_rating=3,  # Decent accuracy
        description=(
            "Small model (74M parameters). Good balance of speed and accuracy. "
            "Recommended default for most users. Fast enough for interactive use."
        ),
    ),
    "small": ModelSpec(
        name="small",
        min_ram_gb=2.5,
        min_vram_gb=2.0,
        speed_rating=4,  # Fast
        quality_rating=3,  # Good accuracy
        description=(
            "Mid-size model (244M parameters). Better accuracy than base with acceptable speed. "
            "Good for professional transcription on standard hardware."
        ),
    ),
    "medium": ModelSpec(
        name="medium",
        min_ram_gb=5.0,
        min_vram_gb=4.0,
        speed_rating=3,  # Moderate
        quality_rating=4,  # Very good accuracy
        description=(
            "Larger model (769M parameters). Significantly better accuracy, slower processing. "
            "Recommended for high-quality transcription when performance is less critical."
        ),
    ),
    "large-v3": ModelSpec(
        name="large-v3",
        min_ram_gb=10.0,
        min_vram_gb=8.0,
        speed_rating=2,  # Slow (but improved in v3)
        quality_rating=5,  # Excellent accuracy
        description=(
            "Largest model (1550M parameters). Best accuracy with latest v3 improvements. "
            "Requires significant compute resources. Use for critical transcription requiring maximum quality."
        ),
    ),
}


def get_model_spec(model_name: str) -> Optional[ModelSpec]:
    """Retrieve specification for a model by name.
    
    Args:
        model_name: Model identifier (e.g., 'base', 'small')
        
    Returns:
        ModelSpec if found, None otherwise
    """
    return MODEL_SPECS.get(model_name)


def list_models() -> list[str]:
    """Get list of available model names in priority order."""
    return list(MODEL_SPECS.keys())


def filter_compatible_models(
    resources: "SystemResources", use_gpu: bool = True
) -> list[ModelSpec]:
    """Filter models that fit within available system resources.
    
    Applies safety margin of 85% available RAM (per design decision) to prevent OOM.
    
    Args:
        resources: Detected system resources (CPU, RAM, GPU)
        use_gpu: Whether to consider GPU when filtering (default: True)
        
    Returns:
        List of compatible ModelSpec instances, sorted by quality (descending)
        then by speed (descending). Empty list if no models fit.
    """
    # Apply 70% safety margin to total RAM to account for system usage and other processes
    safe_ram_gb = resources.total_ram_gb * 0.70
    
    compatible = []
    
    for model_name, spec in MODEL_SPECS.items():
        # Check RAM requirement
        if spec.min_ram_gb > safe_ram_gb:
            logger.debug(f"Model {model_name} requires {spec.min_ram_gb}GB RAM, only {safe_ram_gb:.2f}GB available")
            continue
        
        # Check VRAM requirement if GPU is available and enabled
        if use_gpu and resources.has_gpu and spec.min_vram_gb is not None:
            if resources.available_vram_gb is None:
                # GPU with unified memory (Metal) - VRAM requirement is ignored, use RAM check only
                logger.debug(f"Model {model_name} GPU check skipped (unified memory)")
            elif spec.min_vram_gb > resources.available_vram_gb:
                logger.debug(
                    f"Model {model_name} requires {spec.min_vram_gb}GB VRAM, "
                    f"only {resources.available_vram_gb}GB available"
                )
                continue
        
        # Model is compatible
        compatible.append(spec)
        logger.debug(f"Model {model_name} is compatible")
    
    # Sort by quality descending, then speed descending
    compatible.sort(key=lambda m: (m.quality_rating, m.speed_rating), reverse=True)
    
    logger.info(f"Found {len(compatible)} compatible models")
    return compatible


def recommend_model(
    resources: "SystemResources", use_gpu: bool = True
) -> Tuple[ModelSpec, str]:
    """Recommend the best model for available resources with reasoning.
    
    Selects the highest quality model that fits within available resources.
    Provides human-readable reasoning explanation.
    
    Args:
        resources: Detected system resources
        use_gpu: Whether GPU should be used for model selection
        
    Returns:
        Tuple of (ModelSpec, reasoning_string)
        
    Raises:
        ModelSelectionError: If no compatible models fit available resources
    """
    compatible = filter_compatible_models(resources, use_gpu)
    
    if not compatible:
        # Build error message with details
        safe_ram_gb = resources.total_ram_gb * 0.70
        vram_info = ""
        if resources.has_gpu and resources.available_vram_gb is not None:
            vram_info = f", {resources.available_vram_gb:.2f}GB VRAM"
        elif resources.has_gpu:
            vram_info = " (unified memory)"
        
        error_msg = (
            f"No models fit available resources: {safe_ram_gb:.2f}GB RAM{vram_info} "
            f"({resources.cpu_cores} CPU cores). Smallest model (tiny) requires 1GB RAM."
        )
        logger.error(error_msg)
        raise ModelSelectionError(error_msg)
    
    # Select the highest quality compatible model
    best_model = compatible[0]
    
    # Build reasoning string
    safe_ram_gb = resources.total_ram_gb * 0.70
    reasons = [
        f"System: {resources.cpu_cores} CPU cores, {safe_ram_gb:.2f}GB RAM available",
    ]
    
    if resources.has_gpu:
        if resources.gpu_type == "metal":
            reasons.append(f"GPU: {resources.gpu_type} (unified memory)")
        elif resources.gpu_type and resources.available_vram_gb is not None:
            reasons.append(f"GPU: {resources.gpu_type} ({resources.available_vram_gb:.2f}GB VRAM)")
        use_gpu_str = "using GPU" if use_gpu else "CPU-only mode selected"
        reasons.append(use_gpu_str)
    else:
        reasons.append("No GPU detected, CPU-only mode")
    
    gpu_mode_str = " (GPU mode)" if use_gpu and resources.has_gpu else " (CPU mode)"
    reasons.append(
        f"Recommending '{best_model.name}' model ({best_model.quality_rating}/5 quality, "
        f"{best_model.speed_rating}/5 speed){gpu_mode_str}"
    )
    
    reasoning = " | ".join(reasons)
    logger.info(f"Model recommendation: {best_model.name}")
    logger.debug(f"Reasoning: {reasoning}")
    
    return best_model, reasoning


def get_model_table(
    resources: "SystemResources",
    recommended: Optional[ModelSpec] = None,
    use_gpu: bool = True,
) -> Table:
    """Generate formatted table of all models with compatibility status.
    
    Creates a rich.Table showing all available models with their specifications,
    memory requirements, and compatibility status based on available system resources.
    
    Args:
        resources: Detected system resources (CPU, RAM, GPU)
        recommended: Optional recommended model to highlight
        use_gpu: Whether GPU resources should be considered (default: True)
        
    Returns:
        Rich Table object ready for printing with console.print()
        
    Table Columns:
        - Model: Model name (e.g., 'tiny', 'base')
        - Speed: Speed rating visualization (█ symbols, 1-5 scale)
        - Quality: Quality rating visualization (█ symbols, 1-5 scale)
        - RAM Req: Minimum RAM requirement in GB
        - VRAM Req: Minimum VRAM requirement (GPU only, N/A for CPU)
        - Status: ✓ Recommended, ✓ Compatible, ⚠ Risky, ✗ Incompatible
        
    Status Indicators:
        - ✓ Recommended: This is the recommended model
        - ✓ Compatible: Model fits in available resources
        - ⚠ Risky: Model fits but with <20% safety margin
        - ✗ Incompatible: Model doesn't fit in available resources
    """
    table = Table(title="Available Whisper Models")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Speed", justify="center")
    table.add_column("Quality", justify="center")
    table.add_column("RAM", justify="right")
    table.add_column("VRAM", justify="right")
    table.add_column("Status", justify="center")
    
    # Calculate safe RAM (use 70% of total RAM to account for system usage and other processes)
    # Using total RAM instead of available RAM because available can be too conservative
    safe_ram_gb = resources.total_ram_gb * 0.70
    safe_vram_gb = None
    if use_gpu and resources.has_gpu and resources.available_vram_gb is not None:
        safe_vram_gb = resources.available_vram_gb
    
    # Iterate through all models in order
    for model_name in list_models():
        model = MODEL_SPECS[model_name]
        
        # Generate speed and quality visualizations (filled/empty bars)
        speed_bar = "█" * model.speed_rating + "░" * (5 - model.speed_rating)
        quality_bar = "█" * model.quality_rating + "░" * (5 - model.quality_rating)
        
        # Format memory requirements
        ram_req = f"{model.min_ram_gb:.1f} GB"
        
        if use_gpu and resources.has_gpu:
            if model.min_vram_gb is None:
                vram_req = "N/A"
            else:
                vram_req = f"{model.min_vram_gb:.1f} GB"
        else:
            vram_req = "N/A"
        
        # Determine compatibility status
        ram_compatible = model.min_ram_gb <= safe_ram_gb
        
        # Check VRAM compatibility if GPU is available
        vram_compatible = True
        if use_gpu and resources.has_gpu:
            if model.min_vram_gb is not None:
                if safe_vram_gb is not None:
                    vram_compatible = model.min_vram_gb <= safe_vram_gb
                else:
                    # GPU with unified memory, assume compatible if RAM check passes
                    vram_compatible = ram_compatible
        
        is_compatible = ram_compatible and vram_compatible
        
        # Determine if model is risky (fits but with low margin)
        is_risky = False
        if is_compatible:
            ram_margin = (safe_ram_gb - model.min_ram_gb) / model.min_ram_gb
            if use_gpu and resources.has_gpu and model.min_vram_gb is not None and safe_vram_gb:
                vram_margin = (safe_vram_gb - model.min_vram_gb) / model.min_vram_gb
                is_risky = ram_margin < 0.2 or vram_margin < 0.2
            else:
                is_risky = ram_margin < 0.2
        
        # Generate status string with styling
        if recommended and model.name == recommended.name:
            status = "[green]✓ Recommended[/green]"
        elif is_compatible:
            if is_risky:
                status = "[yellow]⚠ Risky[/yellow]"
            else:
                status = "[green]✓ Compatible[/green]"
        else:
            status = "[red]✗ Incompatible[/red]"
        
        # Add row to table
        table.add_row(
            model.name,
            speed_bar,
            quality_bar,
            ram_req,
            vram_req,
            status,
        )
    
    return table
