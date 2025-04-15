from xclif import command


@command(name="greeter", empty=True)
def _() -> None:
    print("Hello")
