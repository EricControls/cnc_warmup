# gets shown when you run help(cnc_warmup)
"""
CNC Warmup Generator for Heidenhain TNC 640 controllers
"""
__version__ = "0.0.1"

# make imports a little cleaner
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
