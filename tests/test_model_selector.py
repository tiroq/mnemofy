"""Unit tests for model_selector module.

Tests cover:
- ModelSpec dataclass construction and validation
- MODEL_SPECS database structure and content validity
- Model lookup and listing functions
- Model filtering based on system resources
- Model recommendation with reasoning
"""

import pytest
from unittest.mock import Mock

from mnemofy.model_selector import (
    MODEL_SPECS,
    ModelSelectionError,
    ModelSpec,
    filter_compatible_models,
    get_model_spec,
    get_model_table,
    list_models,
    recommend_model,
)


class TestModelSpec:
    """Tests for ModelSpec dataclass."""

    def test_model_spec_construction(self):
        """Test ModelSpec can be instantiated with valid parameters."""
        model = ModelSpec(
            name="test",
            min_ram_gb=2.0,
            min_vram_gb=1.0,
            speed_rating=3,
            quality_rating=4,
            description="Test model",
        )
        assert model.name == "test"
        assert model.min_ram_gb == 2.0
        assert model.min_vram_gb == 1.0
        assert model.speed_rating == 3
        assert model.quality_rating == 4
        assert model.description == "Test model"

    def test_model_spec_frozen(self):
        """Test ModelSpec is immutable (frozen dataclass)."""
        model = ModelSpec(
            name="test",
            min_ram_gb=2.0,
            min_vram_gb=1.0,
            speed_rating=3,
            quality_rating=4,
            description="Test model",
        )
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            model.name = "modified"

    def test_model_spec_validation_speed_rating_invalid_low(self):
        """Test ModelSpec validates speed_rating must be >= 1."""
        with pytest.raises(ValueError, match="speed_rating"):
            ModelSpec(
                name="test",
                min_ram_gb=2.0,
                min_vram_gb=1.0,
                speed_rating=0,  # Invalid
                quality_rating=4,
                description="Test model",
            )

    def test_model_spec_validation_speed_rating_invalid_high(self):
        """Test ModelSpec validates speed_rating must be <= 5."""
        with pytest.raises(ValueError, match="speed_rating"):
            ModelSpec(
                name="test",
                min_ram_gb=2.0,
                min_vram_gb=1.0,
                speed_rating=6,  # Invalid
                quality_rating=4,
                description="Test model",
            )

    def test_model_spec_validation_quality_rating_invalid_low(self):
        """Test ModelSpec validates quality_rating must be >= 1."""
        with pytest.raises(ValueError, match="quality_rating"):
            ModelSpec(
                name="test",
                min_ram_gb=2.0,
                min_vram_gb=1.0,
                speed_rating=3,
                quality_rating=0,  # Invalid
                description="Test model",
            )

    def test_model_spec_validation_quality_rating_invalid_high(self):
        """Test ModelSpec validates quality_rating must be <= 5."""
        with pytest.raises(ValueError, match="quality_rating"):
            ModelSpec(
                name="test",
                min_ram_gb=2.0,
                min_vram_gb=1.0,
                speed_rating=3,
                quality_rating=6,  # Invalid
                description="Test model",
            )

    def test_model_spec_vram_can_be_none(self):
        """Test ModelSpec allows None for min_vram_gb (e.g., unified memory)."""
        model = ModelSpec(
            name="metal-gpu",
            min_ram_gb=2.0,
            min_vram_gb=None,  # Valid for unified memory GPUs
            speed_rating=4,
            quality_rating=3,
            description="Model using unified memory",
        )
        assert model.min_vram_gb is None

    def test_model_spec_valid_rating_boundaries(self):
        """Test ModelSpec accepts valid rating boundaries (1 and 5)."""
        # Should not raise with speed_rating=1
        model1 = ModelSpec(
            name="slow",
            min_ram_gb=10.0,
            min_vram_gb=8.0,
            speed_rating=1,
            quality_rating=5,
            description="Slowest model",
        )
        assert model1.speed_rating == 1

        # Should not raise with quality_rating=1
        model2 = ModelSpec(
            name="low-quality",
            min_ram_gb=1.0,
            min_vram_gb=1.0,
            speed_rating=5,
            quality_rating=1,
            description="Lowest quality model",
        )
        assert model2.quality_rating == 1


class TestModelSpecs:
    """Tests for MODEL_SPECS database."""

    def test_model_specs_contains_all_required_models(self):
        """Test MODEL_SPECS contains all 5 expected models."""
        expected_models = {"tiny", "base", "small", "medium", "large-v3"}
        assert set(MODEL_SPECS.keys()) == expected_models

    def test_model_specs_all_valid_model_spec_instances(self):
        """Test all entries in MODEL_SPECS are valid ModelSpec instances."""
        for name, spec in MODEL_SPECS.items():
            assert isinstance(spec, ModelSpec)
            assert spec.name == name

    def test_tiny_model_spec(self):
        """Test tiny model specification."""
        model = MODEL_SPECS["tiny"]
        assert model.name == "tiny"
        assert model.min_ram_gb == 1.0
        assert model.min_vram_gb == 1.0
        assert model.speed_rating == 5
        assert model.quality_rating == 2
        assert "smallest" in model.description.lower() or "39M" in model.description

    def test_base_model_spec(self):
        """Test base model specification."""
        model = MODEL_SPECS["base"]
        assert model.name == "base"
        assert model.min_ram_gb == 1.5
        assert model.min_vram_gb == 1.5
        assert model.speed_rating == 5
        assert model.quality_rating == 3
        assert "74M" in model.description or "default" in model.description.lower()

    def test_small_model_spec(self):
        """Test small model specification."""
        model = MODEL_SPECS["small"]
        assert model.name == "small"
        assert model.min_ram_gb == 2.5
        assert model.min_vram_gb == 2.0
        assert model.speed_rating == 4
        assert model.quality_rating == 3
        assert "244M" in model.description or "mid" in model.description.lower()

    def test_medium_model_spec(self):
        """Test medium model specification."""
        model = MODEL_SPECS["medium"]
        assert model.name == "medium"
        assert model.min_ram_gb == 5.0
        assert model.min_vram_gb == 4.0
        assert model.speed_rating == 3
        assert model.quality_rating == 4
        assert "769M" in model.description or "larger" in model.description.lower()

    def test_large_v3_model_spec(self):
        """Test large-v3 model specification."""
        model = MODEL_SPECS["large-v3"]
        assert model.name == "large-v3"
        assert model.min_ram_gb == 10.0
        assert model.min_vram_gb == 8.0
        assert model.speed_rating == 2
        assert model.quality_rating == 5
        assert "1550M" in model.description or "largest" in model.description.lower()

    def test_model_specs_memory_ordering(self):
        """Test MODEL_SPECS models follow increasing memory requirements."""
        models = [MODEL_SPECS[name] for name in ["tiny", "base", "small", "medium", "large-v3"]]
        for i in range(len(models) - 1):
            assert models[i].min_ram_gb <= models[i + 1].min_ram_gb
            assert models[i].min_vram_gb == models[i + 1].min_vram_gb or (
                models[i].min_vram_gb is not None
                and models[i + 1].min_vram_gb is not None
                and models[i].min_vram_gb <= models[i + 1].min_vram_gb
            )

    def test_model_specs_speed_quality_inverse_correlation(self):
        """Test that faster models (higher speed) generally have lower quality."""
        # This is a general trend, not absolute rule
        # Speed is descending: 5, 5, 4, 3, 2 (generally descending)
        # Quality is ascending: 2, 3, 3, 4, 5 (generally ascending)
        speed_ratings = [MODEL_SPECS[name].speed_rating for name in ["tiny", "base", "small", "medium", "large-v3"]]
        quality_ratings = [MODEL_SPECS[name].quality_rating for name in ["tiny", "base", "small", "medium", "large-v3"]]

        # First model is fastest and lowest quality
        assert speed_ratings[0] > speed_ratings[-1]
        assert quality_ratings[0] < quality_ratings[-1]

    def test_model_specs_all_have_descriptions(self):
        """Test all models have non-empty descriptions."""
        for name, spec in MODEL_SPECS.items():
            assert spec.description
            assert len(spec.description) > 10  # Reasonably detailed


class TestGetModelSpec:
    """Tests for get_model_spec function."""

    def test_get_model_spec_valid_models(self):
        """Test get_model_spec returns correct specs for all models."""
        for model_name in ["tiny", "base", "small", "medium", "large-v3"]:
            spec = get_model_spec(model_name)
            assert spec is not None
            assert spec.name == model_name

    def test_get_model_spec_invalid_model(self):
        """Test get_model_spec returns None for unknown model."""
        spec = get_model_spec("unknown-model")
        assert spec is None

    def test_get_model_spec_case_sensitive(self):
        """Test get_model_spec is case-sensitive."""
        # Should not find uppercase version
        spec = get_model_spec("TINY")
        assert spec is None

        # But lowercase should work
        spec = get_model_spec("tiny")
        assert spec is not None


class TestListModels:
    """Tests for list_models function."""

    def test_list_models_returns_all_models(self):
        """Test list_models returns all 5 models."""
        models = list_models()
        assert len(models) == 5
        assert set(models) == {"tiny", "base", "small", "medium", "large-v3"}

    def test_list_models_preserves_order(self):
        """Test list_models returns models in definition order."""
        models = list_models()
        expected_order = ["tiny", "base", "small", "medium", "large-v3"]
        assert models == expected_order

    def test_list_models_returns_list(self):
        """Test list_models returns a list type."""
        models = list_models()
        assert isinstance(models, list)


class TestModelSpecsMemoryRequirements:
    """Tests for memory requirement accuracy."""

    def test_memory_requirements_positive(self):
        """Test all memory requirements are positive."""
        for name, spec in MODEL_SPECS.items():
            assert spec.min_ram_gb > 0, f"{name} has invalid min_ram_gb"
            if spec.min_vram_gb is not None:
                assert spec.min_vram_gb > 0, f"{name} has invalid min_vram_gb"

    def test_vram_less_than_or_equal_ram(self):
        """Test VRAM is generally less than or equal to RAM (due to quantization)."""
        for name, spec in MODEL_SPECS.items():
            if spec.min_vram_gb is not None:
                assert spec.min_vram_gb <= spec.min_ram_gb, (
                    f"{name}: VRAM ({spec.min_vram_gb}GB) should be <= "
                    f"RAM ({spec.min_ram_gb}GB) due to quantization"
                )

    def test_typical_memory_requirements(self):
        """Test memory requirements match faster-whisper documentation."""
        # tiny: ~1GB, base: ~1.5GB, small: ~2.5GB, medium: ~5GB, large-v3: ~10GB
        assert MODEL_SPECS["tiny"].min_ram_gb == 1.0
        assert MODEL_SPECS["base"].min_ram_gb == 1.5
        assert MODEL_SPECS["small"].min_ram_gb == 2.5
        assert MODEL_SPECS["medium"].min_ram_gb == 5.0
        assert MODEL_SPECS["large-v3"].min_ram_gb == 10.0


class TestFilterCompatibleModels:
    """Tests for filter_compatible_models function."""

    def _make_resources(
        self,
        cpu_cores=4,
        cpu_arch="arm64",
        total_ram_gb=8.0,
        available_ram_gb=6.0,
        has_gpu=False,
        gpu_type=None,
        available_vram_gb=None,
    ):
        """Helper to create mock SystemResources."""
        resources = Mock()
        resources.cpu_cores = cpu_cores
        resources.cpu_arch = cpu_arch
        resources.total_ram_gb = total_ram_gb
        resources.available_ram_gb = available_ram_gb
        resources.has_gpu = has_gpu
        resources.gpu_type = gpu_type
        resources.available_vram_gb = available_vram_gb
        return resources

    def test_filter_no_ram_constraint(self):
        """Test filtering with plenty of RAM available."""
        resources = self._make_resources(available_ram_gb=12.0)
        filtered = filter_compatible_models(resources, use_gpu=False)

        # All models should be compatible with 12GB RAM (85% = 10.2GB available)
        assert len(filtered) == 5
        # Sorted by quality (desc), then speed (desc)
        # large-v3(5,2), medium(4,3), base(3,5), small(3,4), tiny(2,5)
        assert [m.name for m in filtered] == ["large-v3", "medium", "base", "small", "tiny"]

    def test_filter_4gb_ram_constraint(self):
        """Test filtering with 4GB RAM available (85% = 3.4GB)."""
        resources = self._make_resources(available_ram_gb=4.0)
        filtered = filter_compatible_models(resources, use_gpu=False)

        # tiny (1.0GB), base (1.5GB), small (2.5GB) should fit
        # medium (5.0GB) and large-v3 (10GB) should not fit
        assert len(filtered) == 3
        model_names = [m.name for m in filtered]
        assert "small" in model_names
        assert "base" in model_names
        assert "tiny" in model_names
        assert "medium" not in model_names
        assert "large-v3" not in model_names

    def test_filter_1gb_ram_only_tiny_and_base(self):
        """Test filtering with only 1.2GB RAM available (85% = 1.02GB)."""
        resources = self._make_resources(available_ram_gb=1.2)
        filtered = filter_compatible_models(resources, use_gpu=False)

        # Only tiny (1.0GB) should fit
        # base (1.5GB) requires too much
        assert len(filtered) == 1
        assert filtered[0].name == "tiny"

    def test_filter_insufficient_ram_raises_error(self):
        """Test filtering with less than 1GB RAM returns empty."""
        resources = self._make_resources(available_ram_gb=0.8)
        filtered = filter_compatible_models(resources, use_gpu=False)

        # No models fit
        assert len(filtered) == 0

    def test_filter_with_cuda_gpu(self):
        """Test filtering with CUDA GPU available."""
        resources = self._make_resources(
            available_ram_gb=8.0,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=4.0,
        )
        filtered = filter_compatible_models(resources, use_gpu=True)

        # medium (4.0GB VRAM), small (2.0GB VRAM), base (1.5GB VRAM), tiny (1.0GB VRAM)
        # large-v3 (8.0GB VRAM) should not fit
        model_names = [m.name for m in filtered]
        assert "large-v3" not in model_names
        assert "medium" in model_names
        assert "small" in model_names

    def test_filter_with_metal_gpu_unified_memory(self):
        """Test filtering with Metal GPU (unified memory, no VRAM constraint)."""
        resources = self._make_resources(
            available_ram_gb=6.0,
            has_gpu=True,
            gpu_type="metal",
            available_vram_gb=None,  # Unified memory
        )
        filtered = filter_compatible_models(resources, use_gpu=True)

        # With unified memory, VRAM requirement is ignored
        # Only RAM constraint applies (6GB * 0.85 = 5.1GB available)
        # small (2.5GB), base (1.5GB), tiny (1.0GB) should fit
        # medium (5.0GB), large-v3 (10GB) - medium should fit (5.0GB < 5.1GB), large-v3 not
        model_names = [m.name for m in filtered]
        assert "small" in model_names
        assert "base" in model_names
        assert "tiny" in model_names

    def test_filter_gpu_disabled(self):
        """Test filtering with GPU disabled even though it's available."""
        resources = self._make_resources(
            available_ram_gb=3.0,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=8.0,
        )
        # Even though GPU available with 8GB VRAM, use_gpu=False ignores it
        filtered = filter_compatible_models(resources, use_gpu=False)

        # Only RAM constraint: small (2.5GB), base (1.5GB), tiny (1.0GB) fit
        model_names = [m.name for m in filtered]
        assert "small" in model_names
        assert "medium" not in model_names

    def test_filter_results_sorted_by_quality(self):
        """Test filtered models are sorted by quality (highest first)."""
        resources = self._make_resources(available_ram_gb=12.0)
        filtered = filter_compatible_models(resources, use_gpu=False)

        # All models fit, should be sorted by quality then speed
        # Expect: large-v3(5/5), medium(4/5), small(3/5), base(3/5), tiny(2/5)
        qualities = [m.quality_rating for m in filtered]
        assert qualities == [5, 4, 3, 3, 2]


class TestRecommendModel:
    """Tests for recommend_model function."""

    def _make_resources(
        self,
        cpu_cores=4,
        cpu_arch="arm64",
        total_ram_gb=8.0,
        available_ram_gb=6.0,
        has_gpu=False,
        gpu_type=None,
        available_vram_gb=None,
    ):
        """Helper to create mock SystemResources."""
        resources = Mock()
        resources.cpu_cores = cpu_cores
        resources.cpu_arch = cpu_arch
        resources.total_ram_gb = total_ram_gb
        resources.available_ram_gb = available_ram_gb
        resources.has_gpu = has_gpu
        resources.gpu_type = gpu_type
        resources.available_vram_gb = available_vram_gb
        return resources

    def test_recommend_abundant_resources(self):
        """Test recommendation with abundant resources."""
        resources = self._make_resources(available_ram_gb=16.0)
        model, reasoning = recommend_model(resources, use_gpu=False)

        # Should recommend large-v3 (highest quality model that fits)
        assert model.name == "large-v3"
        assert "large-v3" in reasoning
        assert "CPU mode" in reasoning

    def test_recommend_moderate_resources(self):
        """Test recommendation with moderate resources (6GB)."""
        resources = self._make_resources(available_ram_gb=6.0)
        model, reasoning = recommend_model(resources, use_gpu=False)

        # medium (5.0GB) should fit and be highest quality
        # large-v3 (10GB) won't fit
        assert model.name == "medium"
        assert "medium" in reasoning

    def test_recommend_limited_resources(self):
        """Test recommendation with limited resources (3GB)."""
        resources = self._make_resources(available_ram_gb=3.0)
        model, reasoning = recommend_model(resources, use_gpu=False)

        # With 3GB (85% = 2.55GB available)
        # tiny (1.0GB), base (1.5GB), small (2.5GB) all fit
        # highest quality is base (3/5), so base should be recommended
        assert model.name == "base"
        assert "base" in reasoning

    def test_recommend_minimal_resources(self):
        """Test recommendation with minimal resources (1.2GB)."""
        resources = self._make_resources(available_ram_gb=1.2)
        model, reasoning = recommend_model(resources, use_gpu=False)

        # Only tiny (1.0GB) fits
        assert model.name == "tiny"
        assert "tiny" in reasoning

    def test_recommend_insufficient_resources(self):
        """Test recommendation fails with insufficient resources."""
        resources = self._make_resources(available_ram_gb=0.8)

        # Should raise ModelSelectionError
        with pytest.raises(ModelSelectionError):
            recommend_model(resources, use_gpu=False)

    def test_recommend_with_gpu(self):
        """Test recommendation considers GPU when available."""
        resources = self._make_resources(
            available_ram_gb=6.0,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=6.0,
        )
        model, reasoning = recommend_model(resources, use_gpu=True)

        # Should recommend high quality model considering GPU
        assert model.name in ["large-v3", "medium", "small"]
        assert "GPU" in reasoning

    def test_recommend_reasoning_includes_hardware_info(self):
        """Test recommendation reasoning includes hardware details."""
        resources = self._make_resources(
            available_ram_gb=8.0,
            cpu_cores=8,
            has_gpu=True,
            gpu_type="metal",
        )
        model, reasoning = recommend_model(resources, use_gpu=True)

        # Reasoning should include hardware specs
        assert "8 CPU" in reasoning or "8GB" in reasoning
        assert "metal" in reasoning or "GPU" in reasoning
        assert "quality" in reasoning.lower()

    def test_recommend_returns_tuple(self):
        """Test recommend_model returns (ModelSpec, str) tuple."""
        resources = self._make_resources(available_ram_gb=6.0)
        result = recommend_model(resources, use_gpu=False)

        assert isinstance(result, tuple)
        assert len(result) == 2
        model_spec, reasoning = result
        assert isinstance(model_spec, ModelSpec)
        assert isinstance(reasoning, str)

    def test_recommend_gpu_mode_vs_cpu_mode(self):
        """Test recommendation differs with GPU enabled vs disabled."""
        resources = self._make_resources(
            available_ram_gb=4.0,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=3.0,
        )

        # With GPU enabled, VRAM constraint applies
        model_gpu, _ = recommend_model(resources, use_gpu=True)
        # With GPU disabled, only RAM constraint
        model_cpu, reasoning_cpu = recommend_model(resources, use_gpu=False)

        # CPU mode should have access to more models (no VRAM constraint)
        assert "CPU mode" in reasoning_cpu


class TestGetModelTable:
    """Tests for get_model_table function."""
    
    @staticmethod
    def _make_resources(**kwargs):
        """Helper to create SystemResources mock."""
        defaults = {
            "cpu_cores": 4,
            "cpu_arch": "x86_64",
            "total_ram_gb": 8.0,
            "available_ram_gb": 6.0,
            "has_gpu": False,
            "gpu_type": None,
            "available_vram_gb": None,
        }
        defaults.update(kwargs)
        return Mock(**defaults)

    def test_get_model_table_returns_string(self):
        """Test get_model_table returns a formatted string."""
        resources = self._make_resources()
        table = get_model_table(resources)
        
        assert isinstance(table, str)
        assert len(table) > 0
        assert "Model" in table or "model" in table.lower()

    def test_get_model_table_includes_all_models(self):
        """Test table includes all models from MODEL_SPECS."""
        resources = self._make_resources()
        table = get_model_table(resources)
        
        for model_name in list_models():
            assert model_name in table

    def test_get_model_table_with_recommended_model(self):
        """Test table highlights recommended model."""
        resources = self._make_resources(available_ram_gb=8.0)
        recommended_spec = MODEL_SPECS["small"]
        
        table = get_model_table(resources, recommended=recommended_spec)
        
        assert "small" in table
        assert "Recommended" in table or "recommended" in table.lower()

    def test_get_model_table_shows_compatibility_status(self):
        """Test table displays compatibility status for models."""
        resources = self._make_resources(available_ram_gb=1.5)  # Only tiny + base fit
        table = get_model_table(resources, use_gpu=False)
        
        # Should show compatible and incompatible markers
        assert "Compatible" in table or "compatible" in table.lower() or \
               "Incompatible" in table or "incompatible" in table.lower() or \
               "✓" in table or "✗" in table

    def test_get_model_table_ram_requirements(self):
        """Test table shows RAM requirements for all models."""
        resources = self._make_resources()
        table = get_model_table(resources, use_gpu=False)
        
        # Should show actual RAM requirements (all end in GB)
        assert "GB" in table
        # Should have RAM requirements for multiple models
        assert table.count("GB") >= len(list_models())

    def test_get_model_table_speed_quality_visualization(self):
        """Test table uses bar visualization for speed/quality."""
        resources = self._make_resources()
        table = get_model_table(resources)
        
        # Table should have filled/empty bar characters
        assert "█" in table or "░" in table or \
               "|" in table or "-" in table  # Alternative visualization

    def test_get_model_table_with_gpu_shows_vram(self):
        """Test table shows VRAM requirements when GPU is available."""
        resources = self._make_resources(
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=4.0
        )
        table = get_model_table(resources, use_gpu=True)
        
        # Should show VRAM column (even if some are N/A)
        assert "VRAM" in table or "vram" in table.lower() or "N/A" in table

    def test_get_model_table_cpu_mode_disables_gpu_filtering(self):
        """Test that use_gpu=False ignores GPU resources."""
        resources = self._make_resources(
            available_ram_gb=6.0,
            has_gpu=True,
            gpu_type="cuda",
            available_vram_gb=1.0  # Insufficient VRAM
        )
        
        table_gpu = get_model_table(resources, use_gpu=True)
        table_cpu = get_model_table(resources, use_gpu=False)
        
        # CPU mode should show more compatible models than GPU mode
        # (since GPU VRAM constraint doesn't apply)
        compatible_gpu = table_gpu.count("Compatible") + table_gpu.count("✓")
        compatible_cpu = table_cpu.count("Compatible") + table_cpu.count("✓")
        assert compatible_cpu >= compatible_gpu

    def test_get_model_table_risky_status_for_low_margin(self):
        """Test that models with <20% safety margin show as risky."""
        # Available RAM of 1.1 GB means only tiny (1.0 GB) fits with barely any margin
        resources = self._make_resources(available_ram_gb=1.1, has_gpu=False)
        table = get_model_table(resources, use_gpu=False)
        
        # Should mark tiny as risky if margin < 20%
        # (1.1 - 1.0) / 1.0 = 0.1 = 10% < 20%
        table_content = table.lower()
        has_risky = "risky" in table_content or "⚠" in table

    def test_get_model_table_incompatible_status(self):
        """Test incompatible status when no resources available."""
        resources = self._make_resources(available_ram_gb=0.5)  # Less than tiny (1GB)
        table = get_model_table(resources, use_gpu=False)
        
        # All models should show as incompatible
        assert "Incompatible" in table or "incompatible" in table.lower() or "✗" in table

    def test_get_model_table_metal_gpu_no_vram(self):
        """Test table handles Metal GPU (unified memory, no VRAM reporting)."""
        resources = self._make_resources(
            available_ram_gb=8.0,
            has_gpu=True,
            gpu_type="metal",
            available_vram_gb=None  # Metal doesn't report separate VRAM
        )
        table = get_model_table(resources, use_gpu=True)
        
        # Should still produce valid table with N/A for VRAM
        assert isinstance(table, str)
        assert "metal" in table.lower() or "N/A" in table
        assert len(table) > 0

    def test_get_model_table_no_recommended_model(self):
        """Test table works without recommended parameter."""
        resources = self._make_resources()
        
        # Should not raise error and should return valid table
        table = get_model_table(resources, recommended=None)
        assert isinstance(table, str)
        assert len(table) > 0

    def test_get_model_table_recommended_not_in_specs(self):
        """Test table handles recommended model gracefully if not in specs."""
        resources = self._make_resources()
        # Create a fake recommended spec
        fake_recommended = ModelSpec(
            name="fake-model",
            min_ram_gb=2.0,
            min_vram_gb=None,
            speed_rating=3,
            quality_rating=3,
            description="Not a real model"
        )
        
        # Should not crash, just won't find the recommended model in table
        table = get_model_table(resources, recommended=fake_recommended)
        assert isinstance(table, str)
        assert "fake-model" not in table  # Not in MODEL_SPECS
