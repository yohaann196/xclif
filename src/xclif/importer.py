import importlib
import pkgutil
import types


def get_modules(package: types.ModuleType) -> list[tuple[str, types.ModuleType]]:
    return [
        (name, importlib.import_module(name))
        for _, name, __ in pkgutil.walk_packages(
            package.__path__,
            package.__name__ + ".",
        )
    ]
