# The XClif Manifesto

## The Problem With CLI Frameworks

Building a CLI in Python today means choosing your poison:

- **argparse** — You write parsers by hand, wiring up subparsers to subparsers. Your command tree is scattered across setup code that has nothing to do with logic.
- **Click** — Decorator-based, better, but you still manually assemble the hierarchy. Every command needs `@group.command()`. Subcommand groups are separate objects you have to nest and register.
- **Typer** — Built on Click, so it inherits the same organizational model. Better type inference, but also incredibly slow.

All of these share a fundamental flaw: **the structure of your CLI is defined in code, not in your project layout.** When your app grows, you end up with giant `cli.py` files, or sprawling import chains manually stitching together subcommands. The file tree of your project and the command tree of your CLI are two completely separate things you have to keep in sync yourself.

There's a better way. We've already seen it — in web frameworks.

## The Insight: Routing

Next.js, FastAPI, Rails — they all solved this same organizational problem for web apps. The key insight: **your directory structure is your route map.** A file at `routes/config/set.py` is the handler for `config set`. You don't register it. It just is.

XClif brings this insight to CLI development.

```
myapp/
└── routes/
    ├── __init__.py       →  myapp
    ├── greet.py          →  myapp greet
    └── config/
        ├── __init__.py   →  myapp config
        ├── get.py        →  myapp config get
        └── set.py        →  myapp config set
```

No registration. No boilerplate assembly. Drop a file in the right folder and the command exists.

## The API

The other half of XClif is what goes *inside* those files.

You write a function. You annotate it. XClif reads the annotations and builds the command for you.

```python
# routes/greet.py
from xclif import command

@command()
def _(name: str, template: str = "Hello, {}!") -> None:
    """Greet someone by name."""
    print(template.format(name))
```

That's it. `name` has no default → it's a positional argument. `template` has a default → it's a `--template` option. The docstring becomes the help text. The type annotation determines how the value is parsed. No separate `help=` strings scattered through decorator arguments. The function signature *is* the CLI contract.

## The Principles

**1. Structure is layout.**
The command tree mirrors the file tree. A developer reading the filesystem should immediately understand the CLI's surface area.

**2. Functions are commands.**
A command is just a function. Its signature is its interface. No special CLI objects, no wrapper classes.

**3. Types do the work.**
Python type annotations already express what a parameter is. XClif reads them to handle conversion, validation, and help text — without you specifying anything twice.

**4. Zero boilerplate at the entry point.**
Your `__main__.py` should be three lines. `Cli.from_routes(routes)` and you're done.

**5. Escape hatches exist.**
The filesystem convention is the happy path, not a prison. You can always reach for the lower-level `Command` and `Cli` objects directly when you need to.

## What XClif Is Not

XClif is not trying to replace every CLI framework for every use case. If you have a single-command script with three flags, use argparse. XClif is for **structured, multi-command CLIs** — the kind where the organizational model matters, where you want `myapp config set` and `myapp config get` and `myapp env use` without spending time on plumbing.

It is also not a kitchen sink. XClif will not bundle a logging framework, a plugin system, a configuration management library, or a database ORM. It does one thing: **turn a folder of functions into a CLI.**

## The Goal

The best CLIs feel inevitable. The commands are where you expect them, the options do what you think, the help text tells you what you need. XClif's goal is to make building that kind of CLI the path of least resistance — so you spend your time on logic, not scaffolding.

Ship the CLI you meant to build.
