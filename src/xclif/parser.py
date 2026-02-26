from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from xclif.definition import Option

if TYPE_CHECKING:
    from xclif.command import Command


def _build_alias_map(options: dict[str, Option]) -> dict[str, str]:
    """Build a mapping from short alias → long option name."""
    alias_map: dict[str, str] = {}
    for long_name, option in options.items():
        for alias in option.aliases:
            alias_map[alias] = long_name
    return alias_map


def _parse_token_stream(
    options: dict[str, Option],
    subcommands: dict[str, "Command"],
    args: list[str],
) -> tuple[list[str], dict[str, list], int | None]:
    """Scan a token stream at a single command level.

    Tokens are consumed left to right. Options (--name / -x) are recognised
    and collected regardless of their position relative to positional tokens
    (interspersed options are supported). Scanning stops as soon as a token
    is identified as a subcommand name — that token's index is returned so
    the caller can hand off the tail to the subcommand parser.

    Returns:
        positionals  - raw positional tokens collected in order
        parsed_opts  - dict[name, [value, ...]] for all options seen
        subcmd_index - index into `args` of the subcommand token, or None
    """
    alias_map = _build_alias_map(options)
    positionals: list[str] = []
    parsed_opts: dict[str, list] = defaultdict(list)
    i = 0
    while i < len(args):
        token = args[i]

        if token == "--":
            # Everything after -- is a raw positional
            positionals.extend(args[i + 1 :])
            break

        if token.startswith("--"):
            # Long option: --name value  or  --name=value
            if "=" in token:
                name_part, value = token.split("=", 1)
                name = name_part.removeprefix("--").replace("-", "_")
                try:
                    option = options[name]
                except KeyError as err:
                    msg = f"Unknown option {name_part!r}"
                    raise RuntimeError(msg) from err
                if option.converter is bool:
                    msg = f"Boolean flag {name_part!r} does not take a value"
                    raise RuntimeError(msg)
                parsed_opts[name].append(option.converter(value))
            else:
                name = token.removeprefix("--").replace("-", "_")
                try:
                    option = options[name]
                except KeyError as err:
                    msg = f"Unknown option {token!r}"
                    raise RuntimeError(msg) from err
                if option.converter is bool:
                    parsed_opts[name].append(True)
                else:
                    if i + 1 >= len(args):
                        msg = f"Option {token!r} requires a value"
                        raise RuntimeError(msg)
                    i += 1
                    parsed_opts[name].append(option.converter(args[i]))

        elif token.startswith("-") and len(token) > 1:
            # Short option: -v  or  -n value
            if token not in alias_map:
                msg = f"Unknown option {token!r}"
                raise RuntimeError(msg)
            long_name = alias_map[token]
            option = options[long_name]
            if option.converter is bool:
                parsed_opts[long_name].append(True)
            else:
                if i + 1 >= len(args):
                    msg = f"Option {token!r} requires a value"
                    raise RuntimeError(msg)
                i += 1
                parsed_opts[long_name].append(option.converter(args[i]))

        elif token in subcommands:
            # Subcommand name — stop scanning, hand off tail
            return positionals, parsed_opts, i

        else:
            positionals.append(token)

        i += 1

    return positionals, parsed_opts, None


def parse_and_execute_impl(
    args: list[str],
    command: "Command",
    context: dict | None = None,
) -> int:
    """Parse `args` in the context of `command` and execute.

    `context` carries cascading option values resolved by ancestor commands.
    It is never passed as kwargs to command.run() — it is a separate concern.
    """
    if context is None:
        context = {}

    # Merge all option namespaces for scanning: user options + implicit options.
    # We keep them logically separate (implicit_options vs options on Command)
    # but the scanner needs to see both so it knows the arity of every token.
    all_options = {**command.implicit_options, **command.options}

    positionals, parsed_opts, subcmd_index = _parse_token_stream(
        all_options, command.subcommands, args
    )

    # --- Act on implicit options first, before any dispatch ---

    # --help / -h: print help and exit immediately
    if parsed_opts.get("help"):
        if subcmd_index is not None:
            subcommand = command.subcommands[args[subcmd_index]]
            subcommand.print_long_help()
        else:
            command.print_long_help()
        return 0

    # --version: only present on root command (injected by Cli)
    if parsed_opts.get("version"):
        version = command.version or "unknown"
        print(f"{command.name} {version}")
        return 0

    # Build updated cascading context for children
    new_context = dict(context)
    for name, option in command.implicit_options.items():
        if option.cascading and name in parsed_opts:
            values = parsed_opts[name]
            if option.converter is bool:
                existing = new_context.get(name, 0)
                new_context[name] = existing + len(values)
            else:
                new_context[name] = values[-1]  # last wins

    # --- Dispatch ---

    if subcmd_index is not None:
        subcommand = command.subcommands[args[subcmd_index]]
        return parse_and_execute_impl(args[subcmd_index + 1 :], subcommand, new_context)

    if command.subcommands and not positionals and not _user_opts(parsed_opts, command):
        command.print_short_help()
        return 0

    if command.subcommands and positionals:
        raise RuntimeError(f"Unknown subcommand {positionals[0]!r}")

    # Leaf command: assign positionals and call run()
    declared_args = command.arguments
    variadic_arg = declared_args[-1] if declared_args and declared_args[-1].variadic else None
    fixed_args = declared_args[:-1] if variadic_arg else declared_args

    # Check required fixed args are present
    if len(positionals) < len(fixed_args):
        missing = [a.name for a in fixed_args[len(positionals) :]]
        msg = f"Missing required argument(s): {', '.join(missing)}"
        raise RuntimeError(msg)

    # Convert fixed positional args
    converted_args = [
        arg.converter(raw) for raw, arg in zip(positionals, fixed_args)
    ]

    # Convert variadic remainder
    if variadic_arg:
        remaining = positionals[len(fixed_args) :]
        converted_args.extend(variadic_arg.converter(raw) for raw in remaining)

    # Only user-defined option values go to run()
    user_kwargs: dict = {}
    for name, option in command.options.items():
        if name in parsed_opts:
            values = parsed_opts[name]
            user_kwargs[name] = values if len(values) > 1 else values[0]
        elif option.default is not None:
            user_kwargs[name] = option.default

    return command.run(*converted_args, **user_kwargs) or 0


def _user_opts(parsed_opts: dict, command: "Command") -> bool:
    """Return True if any user-defined options were parsed."""
    return any(k in command.options for k in parsed_opts)
