"""Llama 3.1 via DashScope. Prefer: python -m src.cli run --provider aliyun ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="aliyun")
