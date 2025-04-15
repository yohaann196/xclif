from xclif import WithConfig, command, log


# This would create a command with `name` as an argument and template
# as an option (with an alias of -t).
# Because the types are annotated with WithConfig, the command would be
# able to read the configuration from the config file in the OS data directory or
# from the environment variables.
@command()
def _(name: WithConfig[str], template: WithConfig[str] = "Hello, {}!") -> None:
    log.print(template.format(name))
