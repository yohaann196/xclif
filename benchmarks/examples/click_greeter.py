"""Greeter CLI implemented with Click."""
import click


@click.group()
def cli() -> None:
    """Greeter CLI."""


@cli.command()
@click.argument("name")
@click.option("--greeting", "-g", default="Hello", help="Greeting word")
@click.option("--count", "-c", default=1, type=int, help="Repeat count")
def greet(name: str, greeting: str, count: int) -> None:
    """Greet someone."""
    for _ in range(count):
        click.echo(f"{greeting}, {name}!")


@cli.group()
def config() -> None:
    """Manage configuration."""


@config.command()
@click.argument("key")
@click.argument("value")
def set(key: str, value: str) -> None:
    """Set a config value."""
    click.echo(f"Set {key}={value}")


@config.command("get")
@click.argument("key")
def get_cmd(key: str) -> None:
    """Get a config value."""
    click.echo(f"Get {key}")


if __name__ == "__main__":
    cli()
