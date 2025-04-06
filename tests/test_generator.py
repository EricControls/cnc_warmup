import pytest
from pathlib import Path
from src.cnc_warmup.models import WarmupConfig, Tool
from src.cnc_warmup.warmup_generator import WarmupGenerator


class TestWarmupGenerator:
    @pytest.fixture
    def medium_config(self):
        return WarmupConfig(
            machine_type="medium",
            tool=Tool(number=1, length=100.0, radius=5.0),
            duration_min=30,
            use_coolant=True
        )


    def test_generator_init(self, medium_config):
        generator = WarmupGenerator(medium_config)
        assert generator.config == medium_config
        assert generator.machine.name == "Medium CNC Machine"
        assert generator.machine.x_limits == (-508, 508)


    def test_tool_length_validation(self):
        """Test tool length safety checks"""
        # Valid tool
        config = WarmupConfig(
            machine_type="medium",
            tool=Tool(number=1, length=400, radius=5),
            duration_min=30
        )
        generator = WarmupGenerator(config)
        assert generator is not None

        # Invalid tool (too long)
        config.tool.length = 450
        with pytest.raises(ValueError, match="exceeds 85% of machine Z travel"):
            WarmupGenerator(config)


    def test_gcode_generation(self, medium_config):
        """Test complete g-code output structure"""
        generator = WarmupGenerator(medium_config)
        gcode = generator.generate_gcode()

        assert gcode[0].startswith("BEGIN PGM Medium_CNC_Machine MM")
        assert gcode[-1].startswith("END PGM Medium_CNC_Machine MM")
        assert any(f"TOOL DEF {medium_config.tool.number}" in line for line in gcode)

        # Verify coolant commands
        assert "M8" in "\n".join(gcode)  # coolant ON
        assert "M9" in "\n".join(gcode)  # coolant OFF


    def test_movement_patterns(self, medium_config):
        """Verify movement scaling based on duration"""
        generator = WarmupGenerator(medium_config)
        gcode = generator.generate_gcode()

        cycles = [line for line in gcode if "CYCLE" in line]
        assert len(cycles) == 15 # 30min / 2min per cycle


    def test_all_machine_types(self):
        """Verify all machine types can initialize"""
        for machine, expected_name in [
                ("small", "Small_CNC_Machine"),
                ("medium", "Medium_CNC_Machine"),
                ("large", "Large_CNC_Machine")
        ]:
            config = WarmupConfig(
                machine_type=machine,
                tool=Tool(number=1, length=100),
                duration_min=10
            )

        generator = WarmupGenerator(config)
        assert generator is not None
        assert f"{machine.capitalize()}_CNC_Machine" in generator.generate_gcode()[0]
