from dataclasses import dataclass
from typing import Literal, Tuple


@dataclass
class Tool:
    """CNC tool definition with length compensation support"""
    number: int
    length: float  # in mm
    radius: float = 5.0

    def __post_init__(self):
        if self.length <= 0:
            raise ValueError("Tool length must be positive")
        if self.radius <= 0:
            raise ValueError("Tool radius must be positive")
        if not 1 <= self.number <= 99:
            raise ValueError("Tool number mnust be between 1-99")


@dataclass
class MachineProfile:
    """Machine physical limits and capabilities"""
    name: str
    x_limits: Tuple[float, float]  # (min, max) in mm
    y_limits: Tuple[float, float]
    z_limits: Tuple[float, float]
    max_rpm: int = 16000
    feedrates: Tuple[float, float, float] = (45, 45, 40)  # m/min
    coolant_available: bool = True

    @property
    def feedrate_mm_min(self) -> Tuple[int, int, int]:
        """Convert feedrates from m/min to mm/min"""
        return (
            int(self.feedrates[0] * 1000),  # X
            int(self.feedrates[1] * 1000),  # Y
            int(self.feedrates[2] * 1000)   # Z
        )


@dataclass
class WarmupConfig:
    """User-defined warmup parameters"""
    machine_type: Literal["small", "medium", "large"]
    tool: Tool
    duration_min: int = 30
    start_feed_percent: int = 25  # make this an argument later
    finish_feed_percent: int = 100  # make this an argument later
    start_rpm_percent: int = 25  # make this an argument later
    finish_rpm_percent: int = 100  # make this an argument later
    use_coolant: bool = False

    def __post_init__(self):
        """Validate warmup configurations."""
        if self.duration_min <= 0:
            raise ValueError("Duration must be positive")
        if self.duration_min > 120:
            raise ValueError("Duration cannot exceed 120 minutes")
