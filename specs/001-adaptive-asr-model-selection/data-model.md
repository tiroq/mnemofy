# Data Model: Adaptive ASR Model Selection

**Feature ID**: 001 | **Version**: 1.0 | **Date**: 2026-02-10

## Overview

This document defines the data structures, types, and relationships for the adaptive ASR model selection feature. All entities are designed to be immutable (frozen dataclasses) where possible to ensure predictability and thread safety.

---

## Entity Definitions

### SystemResources

**Purpose**: Represents the hardware capabilities of the current system.

**Type**: `@dataclass(frozen=True)`

**Module**: `src/mnemofy/resources.py`

**Schema**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SystemResources:
    """Hardware capabilities of the current system."""
    
    cpu_cores: int
    """Number of logical CPU cores (includes hyperthreading)."""
    
    cpu_arch: str
    """CPU architecture (e.g., 'x86_64', 'arm64', 'aarch64')."""
    
    total_ram_gb: float
    """Total system RAM in gigabytes (2 decimal precision)."""
    
    available_ram_gb: float
    """Currently available RAM in gigabytes (2 decimal precision)."""
    
    has_gpu: bool
    """Whether a compatible GPU is detected (CUDA, Metal, ROCm)."""
    
    gpu_type: Optional[str]
    """GPU type identifier: 'cuda', 'metal', 'rocm', or None."""
    
    available_vram_gb: Optional[float]
    """Available VRAM in gigabytes (None if not detectable or no GPU)."""
    
    def __str__(self) -> str:
        """Human-readable representation for logging/display."""
        gpu_info = f"{self.gpu_type.upper()}" if self.has_gpu else "None"
        vram_info = f", {self.available_vram_gb:.1f}GB VRAM" if self.available_vram_gb else ""
        return (
            f"CPU: {self.cpu_cores} cores ({self.cpu_arch}), "
            f"RAM: {self.available_ram_gb:.1f}/{self.total_ram_gb:.1f} GB, "
            f"GPU: {gpu_info}{vram_info}"
        )
```

**Constraints**:
- `cpu_cores` must be >= 1
- `total_ram_gb` must be > 0
- `available_ram_gb` must be >= 0 and <= total_ram_gb
- `cpu_arch` must be non-empty string
- `gpu_type` must be one of: `"cuda"`, `"metal"`, `"rocm"`, or `None`
- `available_vram_gb` must be > 0 if provided

**Example Instances**:

```python
# High-end macOS system (Apple Silicon)
SystemResources(
    cpu_cores=8,
    cpu_arch="arm64",
    total_ram_gb=16.0,
    available_ram_gb=14.2,
    has_gpu=True,
    gpu_type="metal",
    available_vram_gb=None  # Unified memory
)

# Linux workstation with NVIDIA GPU
SystemResources(
    cpu_cores=16,
    cpu_arch="x86_64",
    total_ram_gb=32.0,
    available_ram_gb=28.5,
    has_gpu=True,
    gpu_type="cuda",
    available_vram_gb=11.0  # RTX 3080
)

# Low-resource Windows VM
SystemResources(
    cpu_cores=2,
    cpu_arch="x86_64",
    total_ram_gb=4.0,
    available_ram_gb=2.1,
    has_gpu=False,
    gpu_type=None,
    available_vram_gb=None
)
```

---

### ModelSpec

**Purpose**: Specification of a Whisper model's requirements and characteristics.

**Type**: `@dataclass(frozen=True)`

**Module**: `src/mnemofy/model_selector.py`

**Schema**:
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ModelSpec:
    """Specification for a Whisper model variant."""
    
    name: str
    """Model identifier (e.g., 'tiny', 'base', 'small', 'medium', 'large-v3')."""
    
    min_ram_gb: float
    """Minimum RAM required for CPU mode inference (includes safety buffer)."""
    
    min_vram_gb: Optional[float]
    """Minimum VRAM required for GPU mode inference (None if GPU not recommended)."""
    
    speed_rating: int
    """Relative speed rating (1-5, where 5=fastest, 1=slowest)."""
    
    quality_rating: int
    """Relative quality rating (1-5, where 5=best quality, 1=lowest)."""
    
    description: str
    """Human-readable description of model characteristics and use cases."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.name}: speed={self.speed_rating}/5, quality={self.quality_rating}/5, "
            f"RAM≥{self.min_ram_gb}GB"
        )
    
    def fits_in_resources(
        self,
        resources: SystemResources,
        use_gpu: bool = True,
        safety_margin: float = 1.2
    ) -> bool:
        """Check if this model fits in given system resources."""
        # RAM check (with safety margin)
        required_ram = self.min_ram_gb * safety_margin
        if resources.available_ram_gb < required_ram:
            return False
        
        # VRAM check (GPU mode only)
        if use_gpu and resources.has_gpu and self.min_vram_gb:
            if resources.available_vram_gb is None:
                # Can't verify VRAM, but GPU available (e.g., Metal)
                return True
            required_vram = self.min_vram_gb * safety_margin
            if resources.available_vram_gb < required_vram:
                return False
        
        return True
```

**Constraints**:
- `name` must be non-empty, lowercase, alphanumeric + hyphen
- `min_ram_gb` must be > 0
- `min_vram_gb` must be > 0 if provided
- `speed_rating` must be in range [1, 5]
- `quality_rating` must be in range [1, 5]
- `description` must be non-empty

**Example Instances**:

```python
ModelSpec(
    name="tiny",
    min_ram_gb=1.2,
    min_vram_gb=1.2,
    speed_rating=5,
    quality_rating=2,
    description="Fastest model, lowest accuracy. Good for testing or draft transcriptions."
)

ModelSpec(
    name="medium",
    min_ram_gb=5.0,
    min_vram_gb=4.0,
    speed_rating=3,
    quality_rating=4,
    description="Balanced model for most use cases. Good quality with reasonable speed."
)

ModelSpec(
    name="large-v3",
    min_ram_gb=10.0,
    min_vram_gb=8.0,
    speed_rating=2,
    quality_rating=5,
    description="Best quality, slowest speed. Requires high-end hardware (16GB+ RAM recommended)."
)
```

---

### ModelRecommendation

**Purpose**: Result of model recommendation process, including reasoning.

**Type**: `@dataclass(frozen=True)`

**Module**: `src/mnemofy/model_selector.py`

**Schema**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelRecommendation:
    """Result of model recommendation algorithm."""
    
    model: ModelSpec
    """The recommended model."""
    
    reasoning: str
    """Human-readable explanation of why this model was recommended."""
    
    compatible_models: list[ModelSpec]
    """All models that fit in available resources (sorted by quality desc)."""
    
    incompatible_models: list[ModelSpec]
    """All models that do NOT fit (for display purposes)."""
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.model.name}: {self.reasoning}"
```

**Constraints**:
- `model` must be present in `compatible_models`
- `compatible_models` must not be empty (if empty, recommendation should fail before creating this object)
- `reasoning` must be non-empty, start with uppercase, end with period
- `incompatible_models` can be empty list

**Example Instance**:

```python
ModelRecommendation(
    model=ModelSpec(name="medium", ...),
    reasoning="Sufficient RAM (14.2GB available), GPU detected (Metal). Medium model balances quality and speed.",
    compatible_models=[
        ModelSpec(name="large-v3", ...),  # Highest quality
        ModelSpec(name="medium", ...),     # Selected
        ModelSpec(name="small", ...),
        ModelSpec(name="base", ...),
        ModelSpec(name="tiny", ...)
    ],
    incompatible_models=[]  # All models fit
)
```

---

## Model Database

### MODEL_SPECS Constant

**Purpose**: Hardcoded database of all supported Whisper models.

**Type**: `dict[str, ModelSpec]`

**Module**: `src/mnemofy/model_selector.py`

**Definition**:
```python
MODEL_SPECS: dict[str, ModelSpec] = {
    "tiny": ModelSpec(
        name="tiny",
        min_ram_gb=1.2,
        min_vram_gb=1.2,
        speed_rating=5,
        quality_rating=2,
        description="Fastest model, lowest accuracy. Good for testing or draft transcriptions."
    ),
    "base": ModelSpec(
        name="base",
        min_ram_gb=1.5,
        min_vram_gb=1.5,
        speed_rating=5,
        quality_rating=3,
        description="Fast model with decent accuracy. Good for quick transcriptions."
    ),
    "small": ModelSpec(
        name="small",
        min_ram_gb=2.5,
        min_vram_gb=2.0,
        speed_rating=4,
        quality_rating=3,
        description="Balanced model for general use. Reliable accuracy with good speed."
    ),
    "medium": ModelSpec(
        name="medium",
        min_ram_gb=5.0,
        min_vram_gb=4.0,
        speed_rating=3,
        quality_rating=4,
        description="High-quality model for most use cases. Recommended for production transcriptions."
    ),
    "large-v3": ModelSpec(
        name="large-v3",
        min_ram_gb=10.0,
        min_vram_gb=8.0,
        speed_rating=2,
        quality_rating=5,
        description="Best quality, slowest speed. Requires high-end hardware (16GB+ RAM recommended)."
    ),
}
```

**Update Policy**: 
- When faster-whisper adds new models, update MODEL_SPECS
- When memory requirements change, re-benchmark and update
- Document source of requirements (empirical testing, upstream docs)

---

## Relationships

### Entity Relationship Diagram

```text
┌──────────────────┐
│ SystemResources  │
└────────┬─────────┘
         │
         │ detects
         │
         ▼
┌──────────────────────┐       ┌──────────────────┐
│ model_selector.py    │──────▶│ ModelSpec        │
│                      │ uses  │  (from MODEL_SPECS)│
│ - filter_compatible()│       └──────────────────┘
│ - recommend_model()  │                │
└──────────┬───────────┘                │
           │                            │ 1:N
           │ produces                   │
           ▼                            │
┌──────────────────────┐                │
│ ModelRecommendation  │◀───────────────┘
│  - model             │   references
│  - reasoning         │
│  - compatible_models │
│  - incompatible_models│
└──────────────────────┘
```

### Data Flow

1. **Detection Phase**:
   ```
   detect_system_resources() → SystemResources
   ```

2. **Filtering Phase**:
   ```
   SystemResources + MODEL_SPECS → filter_compatible_models() → list[ModelSpec]
   ```

3. **Recommendation Phase**:
   ```
   list[ModelSpec] + SystemResources → recommend_model() → ModelRecommendation
   ```

4. **Selection Phase** (Interactive):
   ```
   ModelRecommendation → ModelMenu.show() → Optional[ModelSpec]
   ```

---

## Type Aliases

**Module**: `src/mnemofy/model_selector.py`

```python
from typing import TypeAlias

ModelName: TypeAlias = str
"""Model identifier (e.g., 'tiny', 'base', 'small', 'medium', 'large-v3')."""

GpuType: TypeAlias = str
"""GPU type: 'cuda', 'metal', or 'rocm'."""
```

---

## Validation Functions

### validate_system_resources

**Signature**:
```python
def validate_system_resources(resources: SystemResources) -> None:
    """Validate SystemResources constraints. Raises ValueError if invalid."""
    if resources.cpu_cores < 1:
        raise ValueError(f"cpu_cores must be >= 1, got {resources.cpu_cores}")
    if resources.total_ram_gb <= 0:
        raise ValueError(f"total_ram_gb must be > 0, got {resources.total_ram_gb}")
    if not (0 <= resources.available_ram_gb <= resources.total_ram_gb):
        raise ValueError(
            f"available_ram_gb ({resources.available_ram_gb}) must be "
            f"between 0 and total_ram_gb ({resources.total_ram_gb})"
        )
    if resources.gpu_type and resources.gpu_type not in ("cuda", "metal", "rocm"):
        raise ValueError(f"Invalid gpu_type: {resources.gpu_type}")
    if resources.available_vram_gb is not None and resources.available_vram_gb <= 0:
        raise ValueError(f"available_vram_gb must be > 0 if provided, got {resources.available_vram_gb}")
```

### validate_model_spec

**Signature**:
```python
def validate_model_spec(spec: ModelSpec) -> None:
    """Validate ModelSpec constraints. Raises ValueError if invalid."""
    if not spec.name or not spec.name.replace("-", "").isalnum():
        raise ValueError(f"Invalid model name: {spec.name}")
    if spec.min_ram_gb <= 0:
        raise ValueError(f"min_ram_gb must be > 0, got {spec.min_ram_gb}")
    if spec.min_vram_gb is not None and spec.min_vram_gb <= 0:
        raise ValueError(f"min_vram_gb must be > 0 if provided, got {spec.min_vram_gb}")
    if not (1 <= spec.speed_rating <= 5):
        raise ValueError(f"speed_rating must be in [1, 5], got {spec.speed_rating}")
    if not (1 <= spec.quality_rating <= 5):
        raise ValueError(f"quality_rating must be in [1, 5], got {spec.quality_rating}")
    if not spec.description:
        raise ValueError("description must be non-empty")
```

---

## Error Types

### InsufficientResourcesError

**Purpose**: Raised when no model fits in available system resources.

**Module**: `src/mnemofy/model_selector.py`

**Definition**:
```python
class InsufficientResourcesError(Exception):
    """Raised when no Whisper model fits in available system resources."""
    
    def __init__(self, resources: SystemResources, min_required_ram_gb: float):
        self.resources = resources
        self.min_required_ram_gb = min_required_ram_gb
        super().__init__(
            f"Insufficient RAM for any Whisper model. "
            f"Available: {resources.available_ram_gb:.1f}GB, "
            f"Minimum required: {min_required_ram_gb:.1f}GB"
        )
```

### ResourceDetectionError

**Purpose**: Raised when system resource detection fails.

**Module**: `src/mnemofy/resources.py`

**Definition**:
```python
class ResourceDetectionError(Exception):
    """Raised when system resource detection fails."""
    
    def __init__(self, component: str, original_error: Exception):
        self.component = component  # "CPU", "RAM", "GPU"
        self.original_error = original_error
        super().__init__(
            f"Failed to detect {component}: {original_error}"
        )
```

---

## Serialization

**Note**: Entities are NOT serialized to disk (aligns with Constitution Principle 8: Explicit Persistence). All data is ephemeral and computed fresh on each invocation.

**If serialization is needed in future** (e.g., for caching):
- Use Pydantic models instead of dataclasses for JSON schema validation
- Serialize to JSON for portability
- Add explicit `--cache-resources` flag (makes persistence explicit)

---

## Testing Strategy

### Unit Tests

```python
# test_resources.py
def test_system_resources_creation():
    """Test SystemResources dataclass creation."""
    resources = SystemResources(
        cpu_cores=8,
        cpu_arch="arm64",
        total_ram_gb=16.0,
        available_ram_gb=14.0,
        has_gpu=True,
        gpu_type="metal",
        available_vram_gb=None
    )
    assert resources.cpu_cores == 8
    assert resources.has_gpu is True

def test_system_resources_validation():
    """Test SystemResources constraint validation."""
    with pytest.raises(ValueError):
        validate_system_resources(SystemResources(
            cpu_cores=0,  # Invalid
            cpu_arch="x86_64",
            total_ram_gb=8.0,
            available_ram_gb=4.0,
            has_gpu=False,
            gpu_type=None,
            available_vram_gb=None
        ))
```

```python
# test_model_selector.py
def test_model_spec_fits_in_resources():
    """Test ModelSpec.fits_in_resources() method."""
    spec = MODEL_SPECS["medium"]
    resources = SystemResources(
        cpu_cores=8,
        cpu_arch="x86_64",
        total_ram_gb=16.0,
        available_ram_gb=14.0,
        has_gpu=False,
        gpu_type=None,
        available_vram_gb=None
    )
    assert spec.fits_in_resources(resources) is True

def test_model_spec_does_not_fit():
    """Test ModelSpec.fits_in_resources() returns False."""
    spec = MODEL_SPECS["large-v3"]
    resources = SystemResources(
        cpu_cores=2,
        cpu_arch="x86_64",
        total_ram_gb=4.0,
        available_ram_gb=2.0,
        has_gpu=False,
        gpu_type=None,
        available_vram_gb=None
    )
    assert spec.fits_in_resources(resources) is False
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-10 | Initial data model definition |

---

## Notes

- All dataclasses use `frozen=True` for immutability
- No persistence layer (ephemeral data only)
- Validation functions raise `ValueError` with descriptive messages
- Type hints are Python 3.9+ compatible (using `Optional`, not `|` union syntax)
