"""Greeter CLI implemented with Typer."""
import typer

app = typer.Typer(help="Greeter CLI.")
config_app = typer.Typer(help="Manage configuration.")
app.add_typer(config_app, name="config")


@app.command()
def greet(
    name: str,
    greeting: str = typer.Option("Hello", "-g", "--greeting", help="Greeting word"),
    count: int = typer.Option(1, "-c", "--count", help="Repeat count"),
) -> None:
    """Greet someone."""
    for _ in range(count):
        typer.echo(f"{greeting}, {name}!")


@config_app.command()
def set(key: str, value: str) -> None:
    """Set a config value."""
    typer.echo(f"Set {key}={value}")


@config_app.command("get")
def get_cmd(key: str) -> None:
    """Get a config value."""
    typer.echo(f"Get {key}")


if __name__ == "__main__":
    app()
