import argparse
import json
from scraping_agent import ScrapingAgent
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint

# NLTK and SSL setup for unstructured
try:
    import nltk
    import ssl
    # Attempt to set unverified context for NLTK downloads if needed
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass # For Python versions that don't have it
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    # Define common NLTK data paths within the venv
    # (though NLTK usually finds these, this can help in some edge cases)
    # nltk_data_path = [
    #     "/Users/visheshyadav/test/market_env/nltk_data",
    #     "/Users/visheshyadav/test/market_env/share/nltk_data",
    #     "/Users/visheshyadav/test/market_env/lib/nltk_data"
    # ]
    # for path in nltk_data_path:
    #     if path not in nltk.data.path:
    #         nltk.data.path.append(path)

    # Check and download NLTK resources needed by unstructured
    required_nltk_resources = {
        "tokenizers/punkt": "punkt", 
        "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger"
    }
    for resource_path, resource_id in required_nltk_resources.items():
        try:
            nltk.data.find(resource_path)
            # rprint(f"[green]NLTK resource '{resource_id}' found.[/green]")
        except nltk.downloader.DownloadError:
            rprint(f"[yellow]NLTK resource '{resource_id}' not found. Attempting download...[/yellow]")
            nltk.download(resource_id, quiet=False) # Set quiet=False for more verbose download output
            rprint(f"[green]NLTK resource '{resource_id}' download attempt finished.[/green]")
except ImportError:
    rprint("[yellow]NLTK library not found. Some 'unstructured' features might not work if it's a dependency.[/yellow]")
except Exception as e:
    rprint(f"[red]An error occurred during NLTK setup: {e}[/red]")


console = Console()

def main():
    parser = argparse.ArgumentParser(description="Web Scraping CLI Tool using ScrapingAgent")
    subparsers = parser.add_subparsers(dest="command", help="Available scraping commands", required=True)

    # Fetch HTML command
    fetch_parser = subparsers.add_parser("fetch-html", help="Fetch the raw HTML content of a URL")
    fetch_parser.add_argument("url", help="The URL to fetch HTML from")
    fetch_parser.add_argument("--max-chars", type=int, default=1000, help="Maximum characters of HTML to display")

    # Extract headlines command
    headlines_parser = subparsers.add_parser("extract-headlines", help="Extract headlines from a URL")
    headlines_parser.add_argument("url", help="The URL to extract headlines from")
    headlines_parser.add_argument("tag", help="The HTML tag for headlines (e.g., h1, h2, a)")
    headlines_parser.add_argument("--css-class", help="Optional CSS class of the headline elements")
    headlines_parser.add_argument("--max-headlines", type=int, default=10, help="Maximum number of headlines to display")

    # Extract text command
    text_parser = subparsers.add_parser("extract-text", help="Extract all paragraph text from a URL")
    text_parser.add_argument("url", help="The URL to extract text from")
    text_parser.add_argument("--max-chars", type=int, default=1000, help="Maximum characters of text to display")

    # Unstructured command (optional)
    unstructured_parser = subparsers.add_parser("extract-unstructured", help="Extract elements using unstructured.io (if installed)")
    unstructured_parser.add_argument("url", help="The URL to process with unstructured")

    args = parser.parse_args()
    agent = ScrapingAgent()

    if args.command == "fetch-html":
        rprint(f"[bold blue]Fetching HTML from:[/bold blue] {args.url}")
        html_content = agent.fetch_html_content(args.url)
        if html_content:
            display_content = html_content[:args.max_chars]
            syntax = Syntax(display_content, "html", theme="monokai", line_numbers=True)
            rprint(Panel(syntax, title="HTML Content", border_style="green"))
            if len(html_content) > args.max_chars:
                rprint(f"[yellow]... (truncated, total {len(html_content)} chars)[/yellow]")
        else:
            rprint("[bold red]Failed to fetch HTML.[/bold red]")

    elif args.command == "extract-headlines":
        rprint(f"[bold blue]Extracting headlines from:[/bold blue] {args.url} (Tag: {args.tag}, Class: {args.css_class or 'Any'})")
        headlines = agent.extract_headlines(args.url, args.tag, args.css_class)
        if headlines:
            rprint(Panel("\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines[:args.max_headlines])]), title="Extracted Headlines", border_style="green"))
            if len(headlines) > args.max_headlines:
                rprint(f"[yellow]... (truncated, total {len(headlines)} headlines found)[/yellow]")
        else:
            rprint("[bold red]No headlines found or failed to fetch page.[/bold red]")

    elif args.command == "extract-text":
        rprint(f"[bold blue]Extracting generic text from:[/bold blue] {args.url}")
        text_content = agent.extract_generic_text(args.url)
        if text_content:
            display_content = text_content[:args.max_chars]
            rprint(Panel(display_content, title="Extracted Text", border_style="green"))
            if len(text_content) > args.max_chars:
                rprint(f"[yellow]... (truncated, total {len(text_content)} chars)[/yellow]")
        else:
            rprint("[bold red]Failed to extract text.[/bold red]")

    elif args.command == "extract-unstructured":
        rprint(f"[bold blue]Processing with unstructured.io (via ScrapingAgent fetch):[/bold blue] {args.url}")
        try:
            # Ensure NLTK data is available (can be run once separately if needed)
            # import nltk
            # try:
            #     nltk.data.find('tokenizers/punkt')
            #     nltk.data.find('taggers/averaged_perceptron_tagger')
            # except nltk.downloader.DownloadError:
            #     print("[yellow]NLTK data not found. Attempting download...[/yellow]")
            #     nltk.download('punkt', quiet=True)
            #     nltk.download('averaged_perceptron_tagger', quiet=True)
            #     print("[green]NLTK data download attempt finished.[/green]")

            elements = agent.extract_with_unstructured(url=args.url) # Pass URL
            
            if elements:
                rprint(f"[green]Successfully extracted {len(elements)} elements using unstructured.[/green]")
                for i, el in enumerate(elements[:5]): # Display first 5 elements
                    rprint(Panel(f"Type: {el.get('type', 'N/A')}\nText: {el.get('text', '')[:200]}...", title=f"Element {i+1}"))
            # Check if the agent returned its own ImportError message
            elif isinstance(elements, dict) and "error" in elements and "unstructured" in elements["error"].lower():
                pass # Error already printed by agent
            elif elements is None and not agent.fetch_html_content(args.url): # Case where fetching html failed first
                 pass # Error already printed by agent
            else:
                rprint("[bold red]No elements extracted by unstructured or an error occurred.[/bold red]")
        except ImportError:
            rprint("[bold red]The 'unstructured' library is not installed. Please run 'pip install \"unstructured[html]\"' to use this feature.[/bold red]")
        except Exception as e:
            rprint(f"[bold red]An error occurred while using unstructured: {e}[/bold red]")

if __name__ == "__main__":
    main() 