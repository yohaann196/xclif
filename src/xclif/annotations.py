import types
from typing import Callable, get_args, get_origin

type ScalarParameterTypes = str | int | float | bool
type ParameterTypes = ScalarParameterTypes | list[ScalarParameterTypes]
_default_converters = {str: str, int: int, float: float, bool: bool}


def annotation2converter[T: ParameterTypes, Y](x: T) -> None | Callable[[T], Y]:
    # Check for list[X] generics (e.g. list[str], list[int])
    origin = get_origin(x)
    if origin is list:
        args = get_args(x)
        if args and args[0] in _default_converters:
            return _default_converters[args[0]]
        return None
    return _default_converters.get(x)


def is_list_type(x) -> bool:
    """Return True if the annotation is a list[X] generic."""
    return get_origin(x) is list
