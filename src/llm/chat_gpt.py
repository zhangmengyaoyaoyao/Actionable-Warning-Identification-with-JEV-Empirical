"""GPT-3.5 via AiHubMix. Prefer: python -m src.cli run --provider gpt ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="gpt")
