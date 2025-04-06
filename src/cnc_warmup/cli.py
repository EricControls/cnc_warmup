#!/usr/bin/env python3
import argparse
import sys
from .models import WarmupConfig, Tool
from .warmup_generator import WarmupGenerator


def validate_positive_float(value: str) -> float:
    """Ensure numeric values are positive"""
    try:
        fval = float(value)
        if fval <= 0:
            raise ValueError(f"{value} must be positive")
        return fval
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def parse_arguments():
    parser = argparse.ArgumentParser(
        description =
        """Generate warmup routines for Heidenhain TNC 640 controllers

            Features:
              - Automatic tool length compensation
              - Progressive spindle RPM ramp-up
              - Machine-specific travel limits
              - Coolant control integration

            Example:
              cnc-warmup medium 3 --tool-length 150 --duration 45 -c -o warmup.h""",
        formatter_class=argparse.RawTextHelpFormatter
)

    # Help argument must come first
    # parser.add_argument(
    #     "-h", "--help",
    #     action="store_true",
    #     help="Show this help message and exit"
    #     )

    # Required arguments
    parser.add_argument(
        "machine_type",
        choices=["small", "medium", "large"],
        help="""Machine size selection:
        small  - 762mm X x 508mm Y x 500mm Z
        medium - 1016mm X x 660mm Y x 500mm Z
        large  - 1270mm X x 508mm Y x 500mm Z"""
    )

    parser.add_argument(
        "tool_number",
        type=int,
        choices=range(1, 100),
        metavar="TOOL_NUM",
        help="Tool number (1-99)"
    )

    # Required tool geometry
    parser.add_argument(
        "--tool-length",
        type=validate_positive_float,
        required=True,
        help="Tool length from gauge line in mm (ex. 120.5)"
    )

    # Optional arguments
    parser.add_argument(
        "--tool-radius",
        type=validate_positive_float,
        default=5.0,
        help="Tool radius in mm (default: 5.0)"
    )

    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=30,
        choices=range(1, 121),
        metavar="MINUTES",
        help="Warmup duration (1-120 minutes, default: 30)"
    )

    parser.add_argument(
        "-c", "--coolant",
        action="store_true",
        help="Enable flood coolant (if machine supports it!)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: prints to console)"
    )

    return parser.parse_args()


def main():
    try:
        args = parse_arguments()
        config = WarmupConfig(
            machine_type=args.machine_type,
            tool=Tool(
                number=args.tool_number,
                length=args.tool_length,
                radius=args.tool_radius
            ),
            duration_min=args.duration,
            use_coolant=args.coolant
        )

        generator = WarmupGenerator(config)
        gcode = generator.generate_gcode()

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write("\n".join(gcode))
                print(f"Chooo buddy! Warmup program saved to {args.output}")
        else:
            print("\n".join(gcode))

    except Exception as e:
        print(f"Aw snap! Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
