"""GLM via BigModel. Prefer: python -m src.cli run --provider glm ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="glm")
