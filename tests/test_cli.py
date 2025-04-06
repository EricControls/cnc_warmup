from click.testing import CliRunner
from src.cnc_warmup.cli import main

def test_cli_help():
    """Test the help output"""
    runner = CliRunner()
    results = runner.invoke(main, ["--help"])
    assert results.exit_code == 0
    assert "Generate customized warmup routines" in results.output
    assert "--tool-length" in results.output


def test_cli_small_machine(tmp_path):
    """Test generating a small machine warmup routine"""
    runner = CliRunner()
    output_file = tmp_path / "small_warmpup.h"

    result = runner.invoke(main, [
        "small", "1",
        "--tool-length", "100",
        "--output", str(output_file)
    ])

    assert result.exit_code == 0
    assert output_file.exists()
    assert "SMALL_MACHINE" in output_file.read_text()


def test_cli_missing_required_args():
    """Test missing required arguments"""
    runner = CliRunner()
    result = runner.invoke(main, ["small"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output
