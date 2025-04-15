import sys
from typing import TYPE_CHECKING, Callable

from xclif.definition import Argument, Option

if TYPE_CHECKING:
    from xclif.command import Command


# TODO: Finish and refactor this to be recursive on the Command
# class lol. We still need to have a crisis over the `--` being a thing
def parse_and_execute_impl(
    args: list[str],
    arguments: list[Argument],
    options: dict[str, Option],
    run: Callable[..., int],
    subcommands: dict[str, "Command"],
) -> int:
    # Parsing CLI subcommands are really easy: it's recursive.
    # Dependency injection can be done very easily as well.

    # There are 4 different types of incantations:
    # 1. The command takes no arguments and no options
    # 2. The command is a namespace with arguments and options
    # 3. The command is a namespace with options only
    # 4. The command has subcommands (cannot have arguments, options are "global" and
    #    are passed to the subcommand, unless configured otherwise)

    # Case 1: No arguments and no options
    # TODO: Exclude default options
    if not arguments and not options:
        # Assert that no extra arguments are passed
        if args:
            msg = f"Unexpected arguments: {args}"
            raise ValueError(msg)
        return run()
    # REFACTOR: The option parsing logic is repeated
    # Case 2: Namespace command
    # Parse arguments first, and then options, unless
    # the user uses `--` to separate them
    if arguments:
        # TODO: Special case arguments (e.g. variadic)
        arguments = [
            arg.converter(raw) for raw, arg in zip(args, arguments, strict=False)
        ]
        options = {}
        # now we start parsing options
        i = len(arguments)  # starting from the first non-argument
        while i < len(args):
            arg = args[i]
            if arg.startswith("-"):
                # TODO: Parse options
                if arg == "--":
                    # XXX: Should it be this or should we use shlex.join?
                    arguments.extend(args[i + 1 :])
                if arg.startswith("--"):
                    snake_case = arg.removeprefix("--").replace("-", "_")
                    options[snake_case] = options[snake_case].converter(arg)
                else:
                    # TODO: get alias
                    ...
                i += 1
            else:
                # Error: unexpected argument
                msg = "Unexpected argument"
                raise RuntimeError(msg)
        # TODO: Handle default options
        return run(*arguments, **options)
    # Case 4: Subcommands
    # Parse global options before subcommands
    options = {}
    i = 0
    while i < len(args):
        arg = args[i]
        # Parse global args
        if args[i].startswith("-"):
            # TODO: Parse options
            # TODO: What about boolean options
            if arg == "--":
                ...
            if arg.startswith("--"):
                snake_case = arg.removeprefix("--").replace("-", "_")
                options[snake_case] = options[snake_case].converter(
                    args[i + 1],
                )
                # TODO: Configure the amount to eat
                i += 2  # Skipped eaten parameter
                continue
            else:
                # TODO: get alias
                ...
            i += 1
        else:  # Break at the first non-option (becomes case 4)
            break
    else:
        # Actually, it's a Case 3: Only options (no subcommands detected)
        return run(**options)
    # TODO: Figure cascading options
    if args[i] in subcommands:
        return subcommands[args[i]].execute(args[i + 1 :])
    # Fuzzy match and raise error about unknown command
    raise RuntimeError
