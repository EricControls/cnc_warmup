from src.cnc_warmup.models import WarmupConfig, Tool
from src.cnc_warmup.machines.medium import PROFILE, custom_movements


def test_medium_profile_limits():
    """Test medium machine physical limits"""
    assert PROFILE.x_limits == (-508, 508)
    assert PROFILE.y_limits == (-330, 330)
    assert PROFILE.z_limits == (-500, 0)
    assert PROFILE.max_rpm == 16000


def test_medium_custom_movements():
    """Test medium machine movement patterns"""
    config = WarmupConfig(
        machine_type="medium",
        tool=Tool(number=1, length=150),
        duration_min=20
    )
    moves = custom_movements(config, safe_z=350)

    assert len(moves) == 4  # 4 linear moves
    assert all("F25000" in line or "F30000" in line for line in moves if "F" in line)
