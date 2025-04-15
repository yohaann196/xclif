from rich import print

from xclif import Cli

from . import routes

cli = Cli.from_routes(routes)
print(cli)
if __name__ == "__main__":
    cli.run()
