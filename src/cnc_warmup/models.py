from dataclasses import dataclass
from typing import Literal, Tuple

@dataclass
class Tool:
    """CNC tool definition with length compensation support"""
    number: int
    length: float # in mm
    radius: float = 5.0

    def __post_init__(self):
        if self.length <= 0:
            raise ValueError("Tool length must be positive")
        if self.radius <= 0:
            raise ValueError("Tool radius must be positive")

@dataclass
class MachineProfile:
    """Machine physical limits and capabilities"""
    name: str
    x_limits: Tuple[float, float] # (min, max) in mm
    y_limits: Tuple[float, float]
    z_limits: Tuple[float, float]
    max_rpm: int = 16000
    feedrates: Tuple[float, float, float] = (45, 45, 40) # m/min
    coolant_available: bool = True

    @property
    def feedrate_mm_min(self) -> Tuple[int, int, int]:
        """Convert m/min to mm/min"""
        return (
            int(self.feedrates[0] * 1000), # X
            int(self.feedrates[1] * 1000), # Y
            int(self.feedrates[2] * 1000)  # Z
    )

@dataclass
class WarmupConfig:
    """User-defined warmup parameters"""
    machine_type: Literal["small", "medium", "large"]
    tool: Tool
    duration_min: int = 30
    use_coolant: bool = False
