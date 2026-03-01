from xclif import command


@command()
def _(name: str, greeting: str = "Hello", count: int = 1) -> None:
    """Greet someone."""
    for _ in range(count):
        print(f"{greeting}, {name}!")
