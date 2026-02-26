"""Integration tests using the greeter experiment.

These tests exercise the full stack: routing, parsing, and execution.
The greeter CLI has:
  - greeter          (root — prints "this is the main command")
  - greeter greet    (name: str, template: str = "Hello, {}!")
  - greeter config   (namespace)
  - greeter config set
  - greeter config get
"""

import pytest

from greeter import routes
from xclif import Cli


@pytest.fixture(scope="module")
def cli():
    return Cli.from_routes(routes)


@pytest.fixture(scope="module")
def root(cli):
    return cli.root_command


# ---------------------------------------------------------------------------
# Root command
# ---------------------------------------------------------------------------


def test_root_executes(root, capsys):
    # The root has subcommands, so invoking it with no args triggers the
    # default action: print short help.
    result = root.execute([])
    assert result == 0
    assert capsys.readouterr().out != ""


def test_root_help_returns_zero(root, capsys):
    result = root.execute(["--help"])
    assert result == 0


# ---------------------------------------------------------------------------
# greeter greet
# ---------------------------------------------------------------------------


def test_greet_with_name(root, capsys):
    result = root.execute(["greet", "Alice"])
    assert result == 0
    out = capsys.readouterr().out
    assert "Alice" in out


def test_greet_default_template(root, capsys):
    root.execute(["greet", "Alice"])
    out = capsys.readouterr().out
    assert "Hello, Alice!" in out


def test_greet_custom_template(root, capsys):
    root.execute(["greet", "Alice", "--template", "Hi, {}!"])
    assert "Hi, Alice!" in capsys.readouterr().out


def test_greet_help_returns_zero(root, capsys):
    result = root.execute(["greet", "--help"])
    assert result == 0


def test_greet_unknown_option_returns_error(root, capsys):
    result = root.execute(["greet", "Alice", "--nonexistent"])
    assert result == 2
    assert "Unknown option" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# greeter config (namespace — no-arg subcommand group)
# ---------------------------------------------------------------------------


def test_config_namespace_help_returns_zero(root, capsys):
    result = root.execute(["config", "--help"])
    assert result == 0


def test_config_set_executes(root):
    result = root.execute(["config", "set"])
    assert result == 0


def test_config_get_executes(root):
    result = root.execute(["config", "get"])
    assert result == 0


def test_unknown_subcommand_returns_error(root, capsys):
    result = root.execute(["doesnotexist"])
    assert result == 2
    assert "Unknown" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Completions (auto-added by Cli)
# ---------------------------------------------------------------------------


def test_completions_subcommand_exists(cli):
    assert "completions" in cli.root_command.subcommands


def test_completions_executes(cli, capsys):
    result = cli.root_command.execute(["completions"])
    assert result == 0


# ---------------------------------------------------------------------------
# New feature integration tests
# ---------------------------------------------------------------------------


def test_greet_equals_form(root, capsys):
    root.execute(["greet", "--template=Hi, {}!", "Alice"])
    assert "Hi, Alice!" in capsys.readouterr().out


def test_root_help_short_flag(root, capsys):
    result = root.execute(["-h"])
    assert result == 0
    assert capsys.readouterr().out != ""


def test_greet_help_short_flag(root, capsys):
    result = root.execute(["greet", "-h"])
    assert result == 0


def test_verbose_before_subcommand(root, capsys):
    result = root.execute(["-v", "greet", "Alice"])
    assert result == 0
    assert "Alice" in capsys.readouterr().out


def test_double_dash_in_greet(root, capsys):
    root.execute(["greet", "--", "--not-a-flag"])
    out = capsys.readouterr().out
    assert "--not-a-flag" in out


def test_version_on_root(cli, capsys):
    result = cli.root_command.execute(["--version"])
    assert result == 0


def test_version_not_on_subcommand(root, capsys):
    """--version should not be recognized on subcommands."""
    result = root.execute(["greet", "--version", "Alice"])
    assert result == 2
    assert "Unknown option" in capsys.readouterr().err
