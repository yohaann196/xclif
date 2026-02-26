# Xclif Option System Design

This document defines the option/argument parsing model for Xclif: what syntax is supported, how options interact with subcommand hierarchies, and the rationale for each decision.

---

## Syntax reference

### Long options (primary form)

```
--flag               # boolean flag → True
--name value         # value option, space-separated
--name=value         # value option, = form (TODO: not yet implemented)
```

Long option names use `kebab-case` on the CLI; they map to `snake_case` in Python. `--dry-run` → `dry_run`.

### Short aliases (planned)

```
-v                   # single-char boolean flag
-n value             # single-char value option
```

Short aliases are either auto-generated (first char of the long name, falling back on subsequent chars to avoid collisions) or explicitly declared via `Annotated` metadata. Short options do **not** support bundling (`-abc` ≠ `-a -b -c`) — this is intentional. Bundling is a source of subtle bugs and is rarely needed in modern CLIs.

### Positional arguments

Positional arguments come before any `--` options. Their order matches the order of parameters in the function signature (left to right, required before optional).

```
myapp greet Alice --template "Hi, {}!"
#              ↑ positional    ↑ option
```

Mixing positionals and options (e.g. `greet --template "Hi!" Alice`) is **not supported**. Options must follow all positional arguments. This keeps parsing unambiguous.

### The `--` separator (planned)

`--` ends option parsing. Everything after it is passed as raw positional arguments. This is the POSIX convention and is necessary for commands that invoke subprocesses.

```
myapp run -- --some-flag-for-subprocess
```

---

## Scoping: how options interact with subcommands

This is the most consequential design decision in Xclif.

### The model: lexical scoping

Xclif uses **lexical scoping** for options. An option belongs to the command level at which it is declared. The parser reads left to right; when it sees a subcommand name, it hands off the remainder of the token stream to that subcommand.

```
myapp --verbose config --format json set KEY VALUE
  ↑                ↑                 ↑
  root-level       config-level      set-level
  option           option            (positional args)
```

This means:

- `--verbose` before `config` is a *root-level* option. It is visible to root and cascades downward (see below).
- `--format` after `config` but before `set` is a *config-level* option. It is only visible to the `config` command and its children.
- The `set` subcommand only sees `KEY VALUE`.

**Cascading**: options defined at a parent level and flagged as cascading are forwarded into the child's execution context. The primary use case is flags like `--verbose`, `--no-color`, and `--dry-run` that should affect the entire hierarchy below where they are set.

Cascading is **opt-in per option**, not automatic. Most options should not cascade — `--format json` on `config` should not silently appear in every nested subcommand.

The implicit options (`--verbose`, `--colors`) are cascading by default, since they are globally meaningful.

### Why not "interspersed options"?

Some CLIs allow options anywhere: `git commit -m msg --amend`. Xclif does not support this for leaf commands (options must follow positional args). The reasons:

1. Unambiguous parsing — no lookahead needed to determine if a token is a positional or an option value.
2. Subcommand-level flags before the subcommand name (`myapp --verbose subcmd`) are unambiguous because `--verbose` can't be a subcommand name.

### Formal grammar (current scope)

```
invocation     ::= program global_opts? subcommand_chain
subcommand_chain ::= (subcommand_name local_opts?)* leaf_invocation?
leaf_invocation  ::= positional_args local_opts?
global_opts    ::= option+
local_opts     ::= option+
option         ::= long_option | short_option
long_option    ::= "--" name ("=" value | " " value)?   # bool options omit value
short_option   ::= "-" char value?
```

---

## Implicit options

These are automatically added to every command and are cascading:

| Option | Short | Type | Behavior |
|---|---|---|---|
| `--help` | `-h` | bool | Print help for the current command and exit |
| `--verbose` | `-v` | bool (repeatable) | Increase log verbosity. Multiple `-v` flags increase level further. |
| `--colors` | (none) | str (`always`\|`never`\|`auto`) | Control ANSI color output |
| `--version` | (none) | bool | Print program version and exit (root only) |

`--verbose` is repeatable: `--verbose --verbose` (or eventually `-vv`) sets verbosity level 2. The parsed value is the count of times the flag appeared.

---

## Current implementation status and known gaps

| Feature | Status |
|---|---|
| `--flag` boolean | ✅ Implemented |
| `--name value` (space form) | ✅ Implemented |
| `--name=value` (equals form) | ❌ Not implemented |
| Short options `-v` | ❌ Not implemented |
| `--` separator | ❌ Not implemented |
| Cascading options | ❌ Parsed at parent level but **silently dropped** before forwarding to subcommand (known bug in `parse_and_execute_impl` line ~121) |
| `--help` / `-h` triggering help | ✅ `--help` works; `-h` check exists but is dead (short options not parsed yet) |
| Repeatable value options (`--tag a --tag b` → list) | ✅ Implemented via `flatten_dict_values` |
| Option bundling (`-abc`) | ✗ Explicitly out of scope |
| Interspersed options with positionals | ✗ Explicitly out of scope |

---

## Open design questions

**Q1: Positional args on namespace commands**

Currently, a command with subcommands cannot also have positional arguments. This is enforced in `Cli.add_command`. Is this the right constraint? Git does this (`git -C /path/to/repo commit`) but it's widely considered confusing. **Proposed: keep the constraint.**

**Q2: Where does `--version` live?**

`--version` is in `IMPLICIT_OPTIONS` so it gets added to every command, but semantically it only makes sense on the root. Should it be root-only? Or should every subcommand report the same version? **Proposed: root-only; strip from subcommands during `from_routes`.**

**Q3: Cascading implementation**

When a parent command parses `--verbose` before seeing a subcommand, it needs to forward that value. Two implementation approaches:

- **A (thread-local/context)**: store cascading values in a context object that child commands read at execution time. Clean but adds a context mechanism.
- **B (injection)**: `parse_and_execute_impl` passes a `cascading: dict` argument down the recursion, merging at each level. Pure and explicit, no shared state.

**Proposed: B.** It's easier to test and reason about.
