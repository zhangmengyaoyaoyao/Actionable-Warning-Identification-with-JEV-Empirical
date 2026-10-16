"""Llama 3.1 via NVIDIA. Prefer: python -m src.cli run --provider nvidia ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="nvidia")
