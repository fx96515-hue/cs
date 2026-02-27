"""Make QA CLI runnable as python -m app.qa."""

from .cli import qa_cli

if __name__ == "__main__":
    qa_cli()
