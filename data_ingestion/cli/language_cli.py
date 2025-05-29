import argparse
from rich.console import Console
from language_agent import LanguageAgent
import os
import click

console = Console()

# Set the API key
os.environ.setdefault("MISTRAL_API_KEY", "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

@click.group()
def cli():
    """Language Agent CLI - Text summarization and explanation using Mistral AI"""
    pass

@cli.command()
@click.argument('text')
@click.option('--max-words', default=150, help='Maximum words in summary')
def summarize(text, max_words):
    """Summarize the given text"""
    agent = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")
    summary = agent.summarize(text, max_words=max_words)
    console.print(f"[bold cyan]Summary:[/bold cyan]\n{summary}")

@cli.command()
@click.argument('text')
@click.option('--audience', default='non-expert', help='Target audience for explanation')
def explain(text, audience):
    """Explain the given text for a specific audience"""
    agent = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")
    explanation = agent.explain(text, target_audience=audience)
    console.print(f"[bold magenta]Explanation:[/bold magenta]\n{explanation}")

def main():
    parser = argparse.ArgumentParser(description="Language Agent CLI for summarizing and explaining text.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Summarize input text")
    summarize_parser.add_argument("text", type=str, help="Text to summarize (quote if contains spaces)")
    summarize_parser.add_argument("--max_words", type=int, default=150, help="Approximate maximum words in summary")

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain input text for a non-expert audience")
    explain_parser.add_argument("text", type=str, help="Text to explain (quote if contains spaces)")
    explain_parser.add_argument("--audience", type=str, default="non-expert", help="Target audience description")

    args = parser.parse_args()
    agent = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

    if args.command == "summarize":
        result = agent.summarize(args.text, max_words=args.max_words)
        console.print(f"[bold cyan]Summary:[/bold cyan]\n{result}")
    elif args.command == "explain":
        result = agent.explain(args.text, target_audience=args.audience)
        console.print(f"[bold magenta]Explanation:[/bold magenta]\n{result}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 