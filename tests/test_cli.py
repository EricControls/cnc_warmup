import pytest
from click.testing import CliRunner
from src.cnc_warmup.cli import main


def assert_program_start(content):
    assert "BEGIN PGM" in content

def test_cli_help():
    """Test the help output"""
    runner = CliRunner()
    results = runner.invoke(main, ["--help"])
    assert results.exit_code == 0
    assert "usage: cli [OPTIONS] MACHINE TOOL_NUMBER" in results.output

def test_cli_missing_required_arguments():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "Error: Missing argument 'MACHINE'" in result.output

    result = runner.invoke(main, ["small"])
    assert result.exit_code != 0
    assert "Error: Missing argument 'TOOL_NUMBER'" in result.output

    result = runner.invoke(main, ["small", "1"])
    assert result.exit_code != 0
    assert "Error: Missing option '--tool-length'" in result.output

def test_cli_generate_small_machine(tmp_path):
    """Test generating a small machine warmup routine"""
    runner = CliRunner()
    output_file = tmp_path / "small_warmpup.h"

    result = runner.invoke(main, [
        "small", "1",
        "--tool-length", "100",
        "--duration", "1"
        "--output", str(output_file)
    ])

    assert result.exit_code == 0
    assert output_file.exists()
    with open(output_file, "r") as f:
        content = f.read()
        assert_program_start(content)
        assert "WARMUP_DURATION_MINUTES = 1" in content
        assert "TOOL DEF 1 L+100.0 R5.0" in content
        assert "X_MAX = 475" in content
        assert "X_MIN = -475" in content
        assert "Y_MAX = 380" in content
        assert "Y_MIN = -380" in content
        assert "Z_MAX = 0" in content
        assert "Z_MIN = -475" in content

def test_cli_generate_medium_machine(tmp_path):
    """Test generating a medium machine warmup routine"""
    runner = CliRunner()
    output_file = tmp_path / "medium_warmpup.h"

    result = runner.invoke(main, [
        "medium", "2",
        "--tool-length", "100",
        "--duration", "1"
        "--output", str(output_file)
    ])

    assert result.exit_code == 0
    assert output_file.exists()
    with open(output_file, "r") as f:
        content = f.read()
        assert_program_start(content)
        assert "WARMUP_DURATION_MINUTES = 1" in content
        assert "TOOL DEF 2 L+100.0 R5.0" in content
        assert "X_MAX = 680" in content
        assert "X_MIN = -680" in content
        assert "Y_MAX = 532" in content
        assert "Y_MIN = -532" in content
        assert "Z_MAX = 0" in content
        assert "Z_MIN = -475" in content

def test_cli_generate_large_machine(tmp_path):
    """Test generating a large machine warmup routine"""
    runner = CliRunner()
    output_file = tmp_path / "large_warmpup.h"

    result = runner.invoke(main, [
        "large", "3",
        "--tool-length", "100",
        "--duration", "1",
        "--output", str(output_file)
    ])

    assert result.exit_code == 0
    assert output_file.exists()
    with open(output_file, "r") as f:
        content = f.read()
        assert_program_start(content)
        assert "WARMUP_DURATION_MINUTES = 1" in content
        assert "TOOL DEF 3 L+100.0 R5.0" in content
        assert "X_MAX = 807" in content
        assert "X_MIN = -807" in content
        assert "Y_MAX = 380" in content
        assert "Y_MIN = -380" in content
        assert "Z_MAX = 0" in content
        assert "Z_MIN = -475" in content
