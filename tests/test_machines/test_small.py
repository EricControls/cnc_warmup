from src.cnc_warmup.models import WarmupConfig, Tool
from src.cnc_warmup.machines.small import PROFILE, custom_movements


def test_small_profile_limits():
    """Test small machine physical limits"""
    assert PROFILE.x_limits == (-381, 381)
    assert PROFILE.y_limits == (-254, 254)
    assert PROFILE.z_limits == (-500, 0)
    assert PROFILE.max_rpm == 16000


def test_small_custom_movements():
    """Test small machine movement patterns"""
    config = WarmupConfig(
        machine_type="small",
        tool=Tool(number=1, length=100),
        duration_min=15
    )
    moves = custom_movements(config, safe_z=400)

    assert len(moves) == 5 # should be 4 linear and 1 circular
    assert any("X+300" in line for line in moves)
    assert any("CIRCLE" in line for line in moves)
