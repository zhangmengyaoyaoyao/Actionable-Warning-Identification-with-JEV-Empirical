"""Llama via local Ollama. Prefer: python -m src.cli run --provider ollama ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="ollama")
