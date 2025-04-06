# gets shown when you run help(cnc_warmup)
"""
CNC Warmup Generator for Heidenhain TNC 640 controllers

Generates programmable warmup routines for machine tools with:
- Configurable duration and intensity
- Machine specific motion profiles
- Safety aware tool handling
"""
__version__ = "0.0.1"
__author__ = "EricControls"
__email__ = "kp61dude@gmail.com"


# make imports a little cleaner for pubic API
from .cli import main
from .models import MachineProfile, Tool, WarmupConfig
from .warmup_generator import WarmupGenerator

# when you import with *
__all__ = [
    'main',
    'MachineProfile',
    'Tool',
    'WarmupConfig',
    'WarmupGenerator'
]
