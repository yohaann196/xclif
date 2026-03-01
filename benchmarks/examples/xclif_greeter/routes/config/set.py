from xclif import command


@command()
def _(key: str, value: str) -> None:
    """Set a config value."""
    print(f"Set {key}={value}")
