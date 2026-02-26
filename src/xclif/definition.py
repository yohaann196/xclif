# TODO: Figure better API
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


# TODO: get name of converter/type for help text
# TODO: figure variadic arguments
@dataclass
class Argument[T]:
    name: str
    converter: Callable[[Any], T]
    description: str

    @property
    def short_description(self) -> str:
        return self.description.splitlines()[0]


# XXX: Inheritance of dataclasses? A parameter super class?
@dataclass
class Option[T]:
    name: str
    converter: Callable[[Any], T]
    description: str
    default: Any = None

    @property
    def short_description(self) -> str:
        return self.description.splitlines()[0]


IMPLICIT_OPTIONS = {
    "help": Option("help", bool, "Show this help message and exit"),
    "verbose": Option("verbose", list, "Change verbosity levels"),
    "colors": Option("colors", str, "Control color output"),
    "version": Option("version", str, "Print program version"),
}
