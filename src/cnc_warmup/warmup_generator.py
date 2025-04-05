 import math
from typing import List
from .models import WarmupConfig, MachineProfile

class WarmupGenerator:
    def __init__(self, config: WarmupConfig):
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

    def _validate_tool_limits(self):
        """Ensure tool can safely operate within machine limits"""
        max_z_travel = abs(self.machine.z_limits[0])
        if self.config.tool.length > max_z_travel * 0.85: # 15% safety margin
            raise ValueError(
                f"Tool length {self.config.tool.length}mm exceeds "
                f"85% of machine Z travel ({max_z_travel}mm)"
            )

    def _calculate_feedrate_adjustment(self) -> float:
        """Dynamically reduce feedrates for long tools"""
        normal_length = 100 # Standard tool length (mm)
        max_recommended = abs(self.machine.z_limits[0]) * 0.7

        if self.config.tool.length <= normal_length:
            return 1.0 # No reduction, feed her the onions!

        # Logarithmic reduction (more aggressive fro very long tools)
        length_ratio = (self.config.tool.length - normal_length) / (max_recommended - normal_length)

        return max(0.5, 1 - (0.5 * math.log10(1 + length_ratio * 9)))

    def generate_gcode(self) -> List[str]:
        """Generates complete warmup routine with tool compensation"""
        safe_z = abs(self.machine.z_limits[0]) - self.config.tool.length
        feed_adjust = self._calculate_feedrate_adjustment()
        cycles = max(1, math.ceil(self.config.duration_min / 2)) # 2 min/cycle

        gcode = [
            f"BEGIN PGM {self.machine.name.replace(' ', '_')} MM",
            f"; TOOL: #{self.config.tool.number} L{self.config.tool.length}mm R{self.config.tool.radius}mm",
            f"; FEEDRATE ADJUSTMENT: {feed_adjust*100:.1f}% (tool length compensation)",
            f"BLK FORM 0.1 Z X+0 Y+0 Z-{max(10, safe_z*0.1):.0f}",
            f"BLK FORM 0.2 X{self.machine.x_limits[1]} Y{self.machine.y_limits[1]} Z+0",
            f"TOOL DEF {self.config.tool.number} L+{self.config.tool.length} R{self.config.tool.radius}",
            f"TOOL CALL {self.config.tool.number} Z S0"
        ]

        if self.config.use_coolant and self.machine.coolant_available:
            gcode.append("M8 ; Flood coolant ON")

        gcode.extend(self._generate_warmup_cycles(safe_z, cycles, feed_adjust))
        gcode.extend(self._generate_cooldown(safe_z, feed_adjust))

        if self.config.use_coolant and self.machine.coolant_available:
            gcode.append("M9  ; Flood coolant OFF")

        gcode.extend([
            f"TOOL CALL {self.config.tool.number} Z S0", # Ensure tool consistency
            "L Z+100 FMAX M91",
            "L X+0 Y+0 FMAX M30",
            f"END PGM {self.machine.name.replace(' ', '_')} MM"
        ])
        return [line for line in gcode if line.strip()] # Remove empty lines

    def _generate_warmup_cycles(self, safe_z: float, cycles: int, feed_adjust: float) -> List[str]:
        """Generate progressive warmup movements"""
        base_feeds = self.machine.feedrate_mm_min
        movements = []

        for cycle in range(cycles):
            intensity = 0.3 + (0.7 * cycle / (cycles-1)) if cycles > 1 else 1.0
            current_feeds = (
                int(base_feeds[0] * feed_adjust * intensity),
                int(base_feeds[1] * feed_adjust * intensity),
                int(base_feeds[2] * feed_adjust * intensity)
            )

            movements.extend([
                f"; --- CYCLE {cycle+1}/{cycles} ({intensity*100:.0f}% intensity) ---",
                f"L X+{int(self.machine.x_limits[1]*0.7*intensity)} "
                f"Y+{int(self.machine.y_limits[1]*0.7*intensity)} "
                f"Z-{int(safe_z*0.5*intensity)} F{current_feeds[1]}",

                f"L X-{int(self.machine.x_limits[1]*0.7*intensity)} "
                f"Y-{int(self.machine.y_limits[1]*0.7*intensity)} "
                f"Z-{int(safe_z*0.7*intensity)} F{current_feeds[1]}",

                f"TOOL CALL {self.config.tool.number} Z S{int(self.machine.max_rpm*intensity)} M3",
                f"L Z-{int(safe_z*0.9*intensity)} F{current_feeds[2]}",
                "M0 ; Pause 10 sec" if cycle < cycles-1 else ""
            ])

        return movements

    def _generate_cooldown(self, safe_z: float, feed_adjust: float) -> List[str]:
        """Generate tool-preserving cooldown sequence"""
        cooldown_feeds = (
            int(self.machine.feedrate_mm_min[0] * feed_adjust * 0.4),
            int(self.machine.feedrate_mm_min[1] * feed_adjust * 0.4),
            int(self.machine.feedrate_mm_min[2] * feed_adjust * 0.4)
        )

        return [
            "; === COOLDOWN PHASE ===",
            f"TOOL CALL {self.config.tool.number} Z S{self.machine.max_rpm//3} M3", # nope, not a typo the '//' does an int division eg. 10//3=3 instead of 10/3=3.3333333333333335
            f"L X+{int(self.machine.x_limits[1]*0.3)} Y+{int(self.machine.y_limits[1]*0.3)} "
            f"Z-{int(safe_z*0.3)} F{cooldown_feeds[1]}",
            "M0 ; Pause 30 sec",

            f"TOOL CALL {self.config.tool.number} Z S{self.machine.max_rpm//6} M3",
            f"L X+{int(self.machine.x_limits[1]*0.15)} Y+{int(self.machine.y_limits[1]*0.15)} "
            f"Z-{int(safe_z*0.15)} F{cooldown_feeds[1]//2}",
            "M0 ; Pause 30 sec"
        ]
