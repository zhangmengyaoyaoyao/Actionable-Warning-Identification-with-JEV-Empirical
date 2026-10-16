"""DeepSeek-R1 via AiHubMix. Prefer: python -m src.cli run --provider deepseek ..."""
from src.cli import run_cli

if __name__ == "__main__":
    run_cli(default_provider="deepseek")
