from ..models import MachineProfile, WarmupConfig
from typing import List

PROFILE = MachineProfile(
    name="Small CNC Machine",
    x_limits=(-381, 381),  # 762mm total X travel
    y_limits=(-254, 254),  # 508mm total Y travel
    z_limits=(-500, 0),    # 500mm Z travel (0=top)
    max_rpm=16000,  # m/min
    feedrates=(45, 45, 40),  # X,Y,Z feedrates in m/min
    coolant_available=True
)


def custom_movements(config: WarmupConfig, safe_z: float) -> List[str]:
    """Override default movements if needed"""
    return [
        f"L X+300 Y+0 Z-{safe_z*0.4:.1f} F20000",
        f"L X-300 Y+0 Z-{safe_z*0.6:.1f} F20000",
        f"L X+0 Y+200 Z-{safe_z*0.5:.1f} F22000",
        f"L X+0 Y-200 Z-{safe_z*0.7:.1f} F22000",
        "CIRCLE X+0 Y+0 R150 DR- F25000"  # Circular interpolation
    ]
