import argparse
from retriever_agent import RetrieverAgent # Assuming it's in the same directory
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import json

console = Console()
DEFAULT_INDEX_PATH_CLI = "cli_faiss_store"

def main():
    parser = argparse.ArgumentParser(description="CLI for the Retriever Agent.")
    parser.add_argument("--index-path", type=str, default=DEFAULT_INDEX_PATH_CLI, 
                        help="Path to the FAISS index directory.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Add text command
    add_parser = subparsers.add_parser("add", help="Add texts to the vector store.")
    add_parser.add_argument("texts", nargs='+', help="The text content(s) to add.")
    add_parser.add_argument("--metadatas", type=str, help='JSON list of metadata dicts. E.g., "[{\"source\":\"doc1\"}]"')

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for similar texts.")
    search_parser.add_argument("query", help="The query text to search for.")
    search_parser.add_argument("-k", "--top_k", type=int, default=3, help="Number of top results to retrieve.")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show information about the vector store.")

    args = parser.parse_args()

    # Initialize agent
    rprint(f"[cyan]Initializing RetrieverAgent with index path: {args.index_path}[/cyan]")
    agent = RetrieverAgent(index_path=args.index_path)

    if args.command == "add":
        parsed_metadatas = None
        if args.metadatas:
            try:
                parsed_metadatas = json.loads(args.metadatas)
                if not isinstance(parsed_metadatas, list):
                    raise ValueError("Metadatas should be a list of dictionaries.")
                if parsed_metadatas and args.texts and len(parsed_metadatas) != len(args.texts):
                    rprint(f"[yellow]Warning: Number of texts ({len(args.texts)}) and metadatas ({len(parsed_metadatas)}) do not match. Metadatas might be applied incorrectly or cause errors.[/yellow]")
            except json.JSONDecodeError as e:
                rprint(f"[red]Error parsing metadatas JSON: {e}. Proceeding without metadatas.[/red]")
            except ValueError as e:
                rprint(f"[red]Error in metadatas format: {e}. Proceeding without metadatas.[/red]")

        rprint(f"[cyan]Adding {len(args.texts)} text(s) to the store...[/cyan]")
        doc_ids = agent.add_texts(args.texts, metadatas=parsed_metadatas)
        rprint(f"[green]Successfully added texts. FAISS chunk IDs: {doc_ids}[/green]")
        rprint(f"[green]Total document chunks in store: {agent.get_document_count()}[/green]")

    elif args.command == "search":
        rprint(f"[cyan]Searching for '{args.query}' (top {args.top_k})...[/cyan]")
        results = agent.search(args.query, k=args.top_k)
        if results:
            table = Table(title=f"Search Results for '{args.query}'")
            table.add_column("Score", style="magenta", justify="right")
            table.add_column("Content", style="green")
            table.add_column("Metadata", style="blue")

            for res in results:
                table.add_row(
                    f"{res['score']:.4f}", 
                    res['content'][:200] + ("..." if len(res['content']) > 200 else ""),
                    json.dumps(res['metadata'], indent=2)
                )
            console.print(table)
        else:
            rprint("[yellow]No results found.[/yellow]")
            
    elif args.command == "info":
        count = agent.get_document_count()
        sources = agent.list_all_chunk_sources()
        info_text = (
            f"[bold]Retriever Agent Store Info[/bold]\n"
            f"Index Path: {args.index_path}\n"
            f"Total Document Chunks: {count}\n"
            f"Known Sources: {(', '.join(sources) if sources else 'N/A')}"
        )
        rprint(Panel(info_text, title="Store Information", border_style="blue"))

if __name__ == "__main__":
    main() 