from dataclasses import dataclass
from typing import Literal

@dataclass
class MachineSpecs:
    """Physical limits of a CNC machine"""
    name: str
    x_limits: tuple[float, float] # (min, max) in mm
    y_limits: tuple[float, float]
    z_limits: tuple[float, float]
    max_rpm: int
    coolant_available: bool = false

@dataclass
class WarmupConfig:
    """User-defined warmup parameters"""
    machine_type: Literal["small", "medium", "large"]
    tool_number: int
    duration_min: int = 30
    use_coolant: bool = true
