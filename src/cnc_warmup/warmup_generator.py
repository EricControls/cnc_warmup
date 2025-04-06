import math
from typing import List
from .models import WarmupConfig, MachineProfile

# Formatting constants
GCODE_HEADER = """BEGIN PGM {machine_name} MM
; TOOL: #{tool_num} L{tool_length}mm R{tool_radius}mm
; FEEDRATE ADJUSTMENT: {feed_adjust:.1f}% (tool length compensation)
BLK FORM 0.1 Z X+0 Y+0 Z-{safe_z:.0f}
BLK FORM 0.2 X{x_max} Y{y_max} Z+0
TOOL DEF {tool_num} L+{tool_length} R{tool_radius}
TOOL CALL {tool_num} Z S0"""

GCODE_FOOTER = """

S0 ; turn off spindle
L Z+100 FMAX M91
L X+0 Y+0 FMAX M30
END PGM {machine_name} MM"""


class WarmupGenerator:
    def __init__(self, config: WarmupConfig):
        """Init with warmup configuration."""
        self.config = config
        self.machine = self._load_machine_profile()
        self._validate_tool_limits()

    def _load_machine_profile(self) -> MachineProfile:
        """Dynamically load machine profile based on config"""
        if self.config.machine_type == "small":
            from .machines.small import PROFILE
        elif self.config.machine_type == "medium":
            from .machines.medium import PROFILE
        else:
            from .machines.large import PROFILE
        return PROFILE

    def _validate_tool_limits(self) -> None:
        """Ensure tool can safely operate within machine limits"""
        max_z_travel = abs(self.machine.z_limits[0])
        safety_margin = 0.85  # 15% safety margin
        if self.config.tool.length > max_z_travel * safety_margin:
            raise ValueError(
                f"Tool length {self.config.tool.length}mm exceeds "
                f"85% of machine Z travel ({max_z_travel}mm)"
            )

    def _calculate_feedrate_adjustment(self) -> float:
        """Calculate feedrate reduction factor for long tools."""
        normal_length = 100  # Standard tool length (mm), this assumed can be optimized.
        max_recommended = abs(self.machine.z_limits[0]) * 0.7

        if self.config.tool.length <= normal_length:
            return 1.0  # No reduction, feed her the onions!

        # Logarithmic reduction (more aggressive fro very long tools)
        length_ratio = (self.config.tool.length - normal_length) / (max_recommended - normal_length)

        return max(0.5, 1 - (0.5 * math.log10(1 + length_ratio * 9)))

    def generate_gcode(self) -> List[str]:
        """Generates complete warmup routine with tool compensation"""
        safe_z = abs(self.machine.z_limits[0]) - self.config.tool.length
        feed_adjust = self._calculate_feedrate_adjustment()

        header = GCODE_HEADER.format(
            machine_name=self.machine.name.replace(" ", "_"),
            tool_num=self.config.tool.number,
            tool_length=self.config.tool.length,
            tool_radius=self.config.tool.radius,
            feed_adjust=feed_adjust*100,
            safe_z=max(10, safe_z*0.1),
            x_max=self.machine.x_limits[1],
            y_max=self.machine.y_limits[1]
        ).split("\n")

        movements = []
        if self.config.use_coolant and self.machine.coolant_available:
            movements.append("M8 ; Flood coolant ON")

        movements.extend(self._generate_warmup_cycles(safe_z, max(1, math.ceil(self.config.duration_min / 2)), feed_adjust))
        movements.extend(self._generate_cooldown(safe_z, feed_adjust))

        if self.config.use_coolant and self.machine.coolant_available:
            movements.append("M9  ; Flood coolant OFF")

        # Format footer
        footer = GCODE_FOOTER.format(
            machine_name=self.machine.name.replace(" ", "_"),
            tool_num=self.config.tool.number
        ).split("\n")

        return [line for line in (*header, *movements, *footer)]

    def _generate_warmup_cycles(self, safe_z: float, cycles: int, feed_adjust: float) -> List[str]:
        """Generate progressive warmup movements"""
        movements = []

        for cycle in range(cycles):
            intensity = 0.3 + (0.7 * cycle / (cycles-1)) if cycles > 1 else 1.0

            # Add a blank line before each new cycle
            movements.append("")

            movements.extend([
                f"; CYCLE {cycle+1}/{cycles} ({intensity*100:.0f}%)",
                self._format_movement(
                    x_dist=0.7*intensity,
                    y_dist=0.7*intensity,
                    z_depth=0.7*intensity,
                    feedrate=self.machine.feedrate_mm_min[1]*feed_adjust*intensity
                ),
                self._format_movement(
                    x_dist=-0.7*intensity,
                    y_dist=-0.7*intensity,
                    z_depth=0.7*intensity,
                    feedrate=self.machine.feedrate_mm_min[1]*feed_adjust*intensity
                ),
                #f"TOOL CALL {self.config.tool.number} Z S{int(self.machine.max_rpm*intensity)} M3",
                f"S{int(self.machine.max_rpm*intensity)} M3",
                f"L Z-{int(safe_z*0.9*intensity)} F{int(self.machine.feedrate_mm_min[2]*feed_adjust*intensity)}",
                "M0 P15" if cycle < cycles-1 else ""  # Pause between cycles
            ])

        return [line for line in movements]

    def _format_movement(self, x_dist: float, y_dist: float, z_depth: float, feedrate: float) -> str:
        """Helper to format movement commands consistently."""
        return (f"L X{int(self.machine.x_limits[1]*x_dist):+d} "
                f"Y{int(self.machine.y_limits[1]*y_dist):+d} "
                f"Z-{int(z_depth*100)} "
                f"F{int(feedrate)}")

    def _generate_cooldown(self, safe_z: float, feed_adjust: float) -> List[str]:
        """Generate tool-preserving cooldown sequence"""
        return [
            "; COOLDOWN PHASE",
            #f"TOOL CALL {self.config.tool.number} Z S{self.machine.max_rpm//3} M3",
            f"S{self.machine.max_rpm//3} M3",
            self._format_movement(
                x_dist=0.3,
                y_dist=0.3,
                z_depth=0.3,
                feedrate=self.machine.feedrate_mm_min[1]*feed_adjust*0.4
            ),
            "M0 P5 ; Auto resume after 5s",
            #f"TOOL CALL {self.config.tool.number} Z S{self.machine.max_rpm//6} M3",
            f"S{self.machine.max_rpm//6} M3",
            self._format_movement(
                x_dist=0.15,
                y_dist=0.15,
                z_depth=0.15,
                feedrate=self.machine.feedrate_mm_min[1]*feed_adjust*0.2
            ),
            "M0 P5 ; Auto resume after 5s"
        ]
