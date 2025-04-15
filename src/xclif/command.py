import inspect
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Callable

from xclif.constants import INITIAL_LEFT_PADDING, NAME_DESC_PADDING, NO_DESC
from xclif.definition import IMPLICIT_OPTIONS, Argument, Option
from xclif.parser import parse_and_execute_impl


# TODO: Warn if run function's name is different from
# the name of the module it is defined in
@dataclass
class Command:
    """A command that can be run."""

    name: str
    run: Callable[..., int]
    arguments: list[Argument] = field(default_factory=list)
    options: dict[str, Option] = field(default_factory=dict)
    subcommands: dict[str, "Command"] = field(default_factory=dict)
    NO_DESC = "No description"

    def __post_init__(self) -> None:
        self.options |= IMPLICIT_OPTIONS

    def print_short_help(self) -> None:
        help_text = (
            (self.short_description + "\n" if self.short_description else "")
            + f"[b][u]Usage[/u]: {self.name}[/] [OPTIONS] ARGS"
            + " ".join(f"[{x.name.upper()}]" for x in self.arguments)
            + "\n\n"
        )

        pad_length = max(
            *(len(x.name) for x in self.arguments),
            *map(len, self.subcommands),
            *(len(x) + 2 for x in self.options),
        )
        if self.subcommands:
            help_text += (
                "[b][u]Subcommands[/u]:[/]\n"
                + "\n".join(
                    (
                        " " * INITIAL_LEFT_PADDING
                        + f"[b]{x[0].ljust(pad_length + NAME_DESC_PADDING)}[/]"
                        + f"[i]{x[1].short_description}[/]"
                        for x in self.subcommands.items()
                    ),
                )
                + "\n\n"
            )

        elif self.arguments:
            help_text += (
                "[b][u]Arguments[/u]:[/]\n"
                # TODO: Vertical align descriptions
                + "\n".join(
                    (
                        " " * INITIAL_LEFT_PADDING
                        + f"[b][{x.name}][/b]".ljust(
                            pad_length + NAME_DESC_PADDING,
                        )
                        + f"[i]{x.description}[/]"
                        for x in self.arguments
                    ),
                )
                + "\n\n"
            )
        longest_option = max(map(len, self.options))
        # TODO: Aliases
        help_text += (
            "[b][u]Options[/u]:[/]\n"
            + "\n".join(
                (
                    "[b]"
                    + " " * INITIAL_LEFT_PADDING
                    + ("--" + x[0]).ljust(pad_length + NAME_DESC_PADDING)
                    + f"[/b][i]{x[1].description}[/]"
                    for x in self.options.items()
                ),
            )
            + "\n\n"
        )
        print(help_text)

    def print_long_help(self) -> None:
        help_text = (
            (self.description + "\n" if self.short_description else "")
            + f"[b][u]Usage[/u]: {self.name}[/] [OPTIONS]"
            + " ".join(f"[{x.name.upper()}]" for x in self.arguments)
            + "\n\n"
        )
        if self.subcommands:
            help_text += (
                "[b][u]Subcommands[/u]:[/]\n"
                + "\n".join(
                    f"{' ' * INITIAL_LEFT_PADDING}[b]{x[0]}[/]{' ' * NAME_DESC_PADDING}[i]{x[1].short_description}[/]"
                    for x in self.subcommands.items()
                )
                + "\n\n"
            )

        elif self.arguments:
            help_text += (
                "[b][u]Arguments[/u]:[/]\n"
                # TODO: Vertical align descriptions
                + "\n".join(
                    f"[b]{' ' * INITIAL_LEFT_PADDING}[{x.name}][/]\n{textwrap.indent(x.description, '      ')}"
                    for x in self.arguments
                )
                + "\n\n"
            )
        # TODO: Aliases
        help_text += (
            "[b][u]Options[/u]:[/]\n"
            + "\n".join(
                f"{' ' * INITIAL_LEFT_PADDING}[b]--{x.name}[/]{' ' * NAME_DESC_PADDING}[i]{x.description}[/]"
                # XXX?
                for x in self.options.values()
            )
            + "\n\n"
        )
        print(help_text)

    # TODO: Finish and refactor this to be recursive on the Command
    # class lol. We still need to have a crisis over the `--` being a thing
    def execute(self, args: list[str] | None = None) -> int:
        return parse_and_execute_impl(
            args or sys.argv[1:],
            self.arguments,
            self.options,
            self.run,
            self.subcommands,
        )

    @property
    def description(self) -> str:
        return inspect.getdoc(self.run) or NO_DESC

    @property
    def short_description(self) -> str:
        return self.description.split("\n")[0]

    # def add_subcommand(self, command: "Command")->None:
    #     if command.name is None:
    #         command.name = command.run.__module__.split(".")[-1]
    #     self.subcommands[command.name] = command
