"""Llama 3.1 via OpenRouter. Prefer: python -m src.cli run --provider openrouter ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="openrouter")
