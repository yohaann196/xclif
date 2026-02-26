import importlib.metadata
import inspect
import sys
import types
from dataclasses import dataclass
from typing import NoReturn, Self

from xclif.command import Command, command
from xclif.definition import Option
from xclif.importer import get_modules

__all__ = ["Cli", "command"]


# TODO: Perhaps Configs could be annotated?
class WithConfig[T]:
    # TODO: polymorphism? file configs? env configs??
    def __class_getitem__(cls, item: T | tuple[T, str]) -> type[T]:
        # For now, as an MVP, WithConfig is not implemented
        if isinstance(item, tuple):
            return item[0]
        return item


def _detect_version(package_name: str) -> str | None:
    """Try to auto-detect the version from installed package metadata."""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


@dataclass
class Cli:
    """The main API for Xclif."""

    root_command: Command
    version: str | None = None

    def __post_init__(self) -> None:
        def completion_func():
            return print("TODO: completions") or 0

        completion_func.__doc__ = "Install completions for your shell"
        self.add_command(["completions"], Command("completions", completion_func))

        # Inject --version as an implicit option on root command only
        self.root_command.implicit_options["version"] = Option(
            "version", bool, "Print program version and exit",
        )
        self.root_command.version = self.version

    def __call__(self) -> NoReturn:
        sys.exit(self.root_command.execute())

    def add_command(self, path: list[str], command: Command) -> None:
        cursor = self.root_command
        for part in path[:-1]:
            if cursor.arguments:
                msg = "Cannot add subcommands to a command with arguments"
                raise ValueError(msg)
            cursor = cursor.subcommands.setdefault(
                part, Command(part, lambda self: self.print_short_help() or 0)
            )
        cursor.subcommands[command.name] = command

    @classmethod
    def from_routes(cls, routes: types.ModuleType, *, version: str | None = None) -> Self:
        members = inspect.getmembers(routes, lambda x: isinstance(x, Command))

        if len(members) > 1:
            msg = f"Multiple commands found in root module ({routes.__name__!r})"
            raise ValueError(msg)
        elif len(members) == 0:
            msg = f"No commands found in root module ({routes.__name__!r})"
            raise ValueError(msg)
        if routes.__package__ is None:
            msg = f"Root module ({routes.__name__!r}) must be part of a package"
            raise ImportError(msg)

        # Auto-detect version if not explicitly provided
        if version is None:
            package_name = routes.__package__.split(".")[0]
            version = _detect_version(package_name)

        root_path = routes.__package__ + "."
        root_command = members[0][1]
        if root_command.name is None:
            msg = "Root command must have a name (it will determine the program name)"
            raise ValueError(msg)
        output = cls(root_command=root_command, version=version)
        for path, module in get_modules(routes):
            members = inspect.getmembers(module, lambda x: isinstance(x, Command))
            if not members:
                continue
            if len(members) > 1:
                msg = f"Multiple commands found in {path!r}"
                raise ValueError(msg)
            _name, function = members[0]
            output.add_command(path.removeprefix(root_path).split("."), function)
        return output
