## Design choices and justification

- Decorator and type-hint based API are superior to imperative or class-based approaches.
- TODO: ok..? having the descriptions (or at least short descriptions) of the parameters in the type annotation might be unreadable. decorators for that? what about aliases??
- File-based "routing"
- `__init__.py` required to differentiate new subcommands ig??
- TODO to test: use singleton to register subcommands versus from_routes
