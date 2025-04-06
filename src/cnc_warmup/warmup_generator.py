import math
from typing import List
from .models import WarmupConfig, MachineProfile

# Formatting constants
GCODE_HEADER = """BEGIN PGM {machine_name} MM

;-- Clear Moves --
L Z+0 RO FMAX ; Ensure Z is fully retracted
L X+0 Y+0 RO FMAX ; Move to machine origin (center-top)
M5 ; Stop spindle

;-- Tool Definition --
; Tool: #{tool_num} L{tool_length}mm R{tool_radius}mm
; Feedrate Adjustment: {feed_adjust:.1f}% (tool length compensation)
TOOL DEF {tool_num} L+{tool_length} R{tool_radius}
TOOL CALL {tool_num} Z S0

;-- Warmup Parameter --
START_FEED_PERCENT = {start_feed_percent}
FINISH_FEED_PERCENT = {finish_feed_percent}
START_RPM_PERCENT = {start_rpm_percent}
FINISH_RPM_PERCENT = {finish_rpm_percent}
WARMUP_DURATION_MINUTES = {duration_min}

;-- Machine Limit (using {safety_margin:.0f}% of travels to stay away from limits) --
X_MAX = {x_max:.0f}
X_MIN = {x_min:.0f}
Y_MAX = {y_max:.0f}
Y_MIN = {y_min:.0f}
Z_MAX = {z_max:.0f}
Z_MIN = -{z_min:.0f}

;-- Feedrate adjusted to {feed_adjust:.1f}% (tool length compensation) --
MAX_FEED_X = {x_max_feedrate:.0f}
MAX_FEED_Y = {y_max_feedrate:.0f}
MAX_FEED_Z = {z_max_feedrate:.0f}
MAX_RPM = {spindle_max_rpm:.0f}"""

GCODE_COOLANT_ON = """
M8 ; Turn on flood coolant"""

GCODE_MOVEMENTS_TEMPLATE = """
;-- Calculate Total Steps (Approximate) --
TOTAL_WARMUP_SECONDS = WARMUP_DURATION_MINUTES * 60
APPROX_CYCLE_TIME = 10 ; Approximate time for one full XYZ cycle (adjust based on travel and feed)
NUM_CYCLES = MAX(1, ROUND(TOTAL_WARMUP_SECONDS / APPROX_CYCLE_TIME)) ; Ensure at least one cycle

;-- Calculate Step Increments --
FEED_INCREMENT_PERCENT = (FINISH_FEED_PERCENT - START_FEED_PERCENT) / NUM_CYCLES
RPM_INCREMENT_PERCENT = (FINISH_RPM_PERCENT - START_RPM_PERCENT) / NUM_CYCLES

;-- Simultaneous Axis & Spindle Warmup (Time-Based Cycles) --
CURRENT_FEED_PERCENT = START_FEED_PERCENT
CURRENT_RPM_PERCENT = START_RPM_PERCENT

FOR CYCLE = 1 TO NUM_CYCLES
  CURRENT_FEED = MAX_FEED_X * CURRENT_FEED_PERCENT / 100
  CURRENT_RPM = MAX_RPM * CURRENT_RPM_PERCENT / 100

  M3 S+ROUND(CURRENT_RPM) ; Start/Adjust Spindle RPM

  L X+X_MIN Y+Y_MIN Z+Z_MIN F=ROUND(CURRENT_FEED) ; Move to near bottom corner
  L X+X_MAX Y+Y_MAX Z+Z_MAX F=ROUND(CURRENT_FEED) ; Move to near top corner
  L X+X_MIN Y+Y_MIN Z+Z_MIN F=ROUND(CURRENT_FEED) ; Move back to near bottom corner

  CURRENT_FEED_PERCENT = CURRENT_FEED_PERCENT + FEED_INCREMENT_PERCENT
  CURRENT_RPM_PERCENT = CURRENT_RPM_PERCENT + RPM_INCREMENT_PERCENT
ENDFOR

M5 ; Stop Spindle"""

GCODE_COOLANT_OFF = """M9 ; Turn off flood coolant
M0 P20 ; dwell for 20s to allow coolant to settle"""

GCODE_FINAL_MOVEMENTS_TEMPLATE = """
;-- Single Axis Sweeps (at finish feed) --
;-- Prevent cold drops of coolant on back of neck --
;-- Knock off some coolant in case operator opens door as soon as program ends --
FINISH_FEED_X = MAX_FEED_X * FINISH_FEED_PERCENT / 100
FINISH_FEED_Y = MAX_FEED_Y * FINISH_FEED_PERCENT / 100
FINISH_FEED_Z = MAX_FEED_Z * FINISH_FEED_PERCENT / 100

L X+X_MIN Y+0 Z+0 F+FINISH_FEED_X
L X+X_MAX F+FINISH_FEED_X
L X+X_MIN F+FINISH_FEED_X

L X+0 Y+Y_MIN Z+0 F+FINISH_FEED_Y
L Y+Y_MAX F+FINISH_FEED_Y
L Y+Y_MIN F+FINISH_FEED_Y

L X+0 Y+0 Z+Z_MIN F+FINISH_FEED_Z
L Z+Z_MAX F+FINISH_FEED_Z
L Z+Z_MIN F+FINISH_FEED_Z"""

GCODE_FOOTER = """
;-- End of Program --
L Z+0 RO FMAX
L X+0 Y+0 RO FMAX
M30 ; Reset spindle rotation

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
        safety_margin = 0.90  # 10% safety margin
        if self.config.tool.length > max_z_travel * safety_margin:
            raise ValueError(
                f"Tool length {self.config.tool.length}mm exceeds "
                f"90% of machine Z travel ({max_z_travel}mm)"
            )

    def _calculate_feedrate_adjustment(self) -> float:
        """Calculate feedrate reduction factor for long tools."""
        normal_length = 100  # Standard tool length (mm), this assumed can be optimized.
        max_recommended = abs(self.machine.z_limits[0]) * 0.90

        if self.config.tool.length <= normal_length:
            return 1.0  # No reduction, feed her the onions!

        # Logarithmic reduction (more aggressive fro very long tools)
        length_ratio = (self.config.tool.length - normal_length) / (max_recommended - normal_length)

        return max(0.5, 1 - (0.5 * math.log10(1 + length_ratio * 9)))

    def generate_gcode(self) -> List[str]:
        """Generates complete warmup routine with tool compensation"""
        adjusted_for_tool_length_z = abs(self.machine.z_limits[0]) - self.config.tool.length
        safety_margin = 0.95  # use most of the travel to stay away from limits switches
        feed_adjust = self._calculate_feedrate_adjustment()

        # Format header
        header = GCODE_HEADER.format(
            machine_name=self.machine.name.replace(" ", "_"),
            tool_num=self.config.tool.number,
            tool_length=self.config.tool.length,
            tool_radius=self.config.tool.radius,
            feed_adjust=feed_adjust*100,
            start_feed_percent=self.config.start_feed_percent,
            finish_feed_percent=self.config.finish_feed_percent,
            start_rpm_percent=self.config.start_rpm_percent,
            finish_rpm_percent=self.config.finish_rpm_percent,
            duration_min=self.config.duration_min,
            safety_margin=safety_margin*100,
            x_max=self.machine.x_limits[1]*safety_margin,
            x_min=self.machine.x_limits[0]*safety_margin,
            y_max=self.machine.y_limits[1]*safety_margin,
            y_min=self.machine.y_limits[0]*safety_margin,
            z_min=adjusted_for_tool_length_z if adjusted_for_tool_length_z < 0 else 0,  # Ensure Z_MIN is negative or zero
            z_max=self.machine.z_limits[1],
            x_max_feedrate=self.machine.feedrate_mm_min[0]*feed_adjust,
            y_max_feedrate=self.machine.feedrate_mm_min[1]*feed_adjust,
            z_max_feedrate=self.machine.feedrate_mm_min[2]*feed_adjust,
            spindle_max_rpm=self.machine.max_rpm*feed_adjust
        ).split("\n")

        # Format body
        body = []
        if self.config.use_coolant and self.machine.coolant_available:
            body.append(GCODE_COOLANT_ON)

        body.append(GCODE_MOVEMENTS_TEMPLATE)

        if self.config.use_coolant and self.machine.coolant_available:
            body.append(GCODE_COOLANT_OFF)

        body.append(GCODE_FINAL_MOVEMENTS_TEMPLATE)

        # Format footer
        footer = GCODE_FOOTER.format(
            machine_name=self.machine.name.replace(" ", "_")
        ).split("\n")

        return [line for line in (*header, *body, *footer)]
