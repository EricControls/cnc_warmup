from src.cnc_warmup.models import WarmupConfig, Tool
from src.cnc_warmup.machines.large import PROFILE, custom_movements

def test_large_profile_limits():
    """Test large machine physical limits"""
    assert PROFILE.x_limits == (-635, 635)
    assert PROFILE.y_limits == (-254, 254)
    assert PROFILE.coolant_available is True

def test_large_diagonal_movements():
    """Test large machine diagonal patterns"""
    config = WarmupConfig(
        machine_type="large",
        tool=Tool(number=1, length=200),
        duration_min=30
    )
    moves = custom_movements(config, safe_z=300)

    assert len(moves) == 6  # Includes diagonal moves
    assert any("X+600 Y+200" in line for line in moves)
    assert any("X-600 Y-200" in line for line in moves)
