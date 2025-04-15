# TODO: use polymorphic type models
from typing import Callable

type ScalarParameterTypes = str | int | float | bool
type ParameterTypes = ScalarParameterTypes | list[ScalarParameterTypes]
_default_converters = {str: str}


# TODO: plugin system
def annotation2converter[T: ParameterTypes, Y](x: T) -> None | Callable[[T], Y]:
    return _default_converters.get(x)
