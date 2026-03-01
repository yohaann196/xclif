from xclif import command


@command("get")
def _(key: str) -> None:
    """Get a config value."""
    print(f"Get {key}")
