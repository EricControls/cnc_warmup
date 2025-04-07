BEGIN PGM Small_CNC_Machine MM

;-- Clear Moves --
L Z+0 RO FMAX ; Ensure Z is fully retracted
L X+0 Y+0 RO FMAX ; Move to machine origin (center-top)
M5 ; Stop spindle

;-- Tool Definition --
; Tool: #3 L50.0mm R7.0mm
; Feedrate Adjustment: 100.0% (tool length compensation)
TOOL DEF 3 L+50.0 R7.0
TOOL CALL 3 Z S0

;-- Warmup Parameter --
START_FEED_PERCENT = 25
FINISH_FEED_PERCENT = 100
START_RPM_PERCENT = 25
FINISH_RPM_PERCENT = 100
WARMUP_DURATION_MINUTES = 34

;-- Machine Limit (using 95% of travels to stay away from limits) --
X_MAX = 362
X_MIN = -362
Y_MAX = 241
Y_MIN = -241
Z_MAX = 0
Z_MIN = -0

;-- Feedrate adjusted to 100.0% (tool length compensation) --
MAX_FEED_X = 45000
MAX_FEED_Y = 45000
MAX_FEED_Z = 40000
MAX_RPM = 16000

M8 ; Turn on flood coolant

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

M5 ; Stop Spindle
M9 ; Turn off flood coolant
M0 P20 ; dwell for 20s to allow coolant to settle

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
L Z+Z_MIN F+FINISH_FEED_Z

;-- End of Program --
L Z+0 RO FMAX
L X+0 Y+0 RO FMAX
M30 ; Reset spindle rotation

END PGM Small_CNC_Machine MM