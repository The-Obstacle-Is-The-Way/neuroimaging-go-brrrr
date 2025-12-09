"""
Tests for the CLI.

These tests verify that the CLI is properly wired up and commands are registered,
without actually running the full dataset processing pipelines.
"""

from pathlib import Path

from typer.testing import CliRunner

from bids_hub.cli import app

runner = CliRunner()


class TestCliHelp:
    """Tests for CLI help output."""

    def test_main_help(self) -> None:
        """Test that main --help works."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "arc" in result.stdout.lower()
        assert "isles24" in result.stdout.lower()
        assert "list" in result.stdout.lower()

    def test_build_help(self) -> None:
        """Test that arc build --help works."""
        result = runner.invoke(app, ["arc", "build", "--help"])

        assert result.exit_code == 0
        assert "ARC" in result.stdout or "arc" in result.stdout.lower()
        assert "--hf-repo" in result.stdout
        assert "--dry-run" in result.stdout

    def test_info_help(self) -> None:
        """Test that arc info --help works."""
        result = runner.invoke(app, ["arc", "info", "--help"])

        assert result.exit_code == 0


class TestCliCommands:
    """Tests for CLI command execution."""

    def test_build_raises_file_not_found_without_participants(self, tmp_path: Path) -> None:
        """Test that build command raises FileNotFoundError when participants.tsv is missing."""
        result = runner.invoke(
            app,
            [
                "arc",
                "build",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should fail because participants.tsv doesn't exist
        assert result.exit_code != 0
        # Exception is captured in result.exception, not stdout
        assert isinstance(result.exception, FileNotFoundError)
        assert "participants.tsv" in str(result.exception)

    def test_build_missing_bids_root_fails(self) -> None:
        """Test that build command fails when bids_root is not provided."""
        result = runner.invoke(
            app,
            [
                "arc",
                "build",
                # Missing bids_root argument
                "--hf-repo",
                "test/test-repo",
            ],
        )

        assert result.exit_code != 0

    def test_info_command_works(self) -> None:
        """Test that info command executes successfully."""
        result = runner.invoke(app, ["arc", "info"])

        assert result.exit_code == 0
        assert "Aphasia Recovery Cohort" in result.stdout
        assert "ds004884" in result.stdout
        assert "CC0" in result.stdout


class TestCliOutput:
    """Tests for CLI output messages."""

    def test_build_shows_processing_message(self, tmp_path: Path) -> None:
        """Test that build shows processing message before failing."""
        result = runner.invoke(
            app,
            [
                "arc",
                "build",
                str(tmp_path),
                "--hf-repo",
                "test/test-repo",
                "--dry-run",
            ],
        )

        # Should show processing message even if it fails later
        assert "Processing ARC" in result.stdout or "ARC" in result.stdout
