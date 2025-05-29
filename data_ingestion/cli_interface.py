# MARKET AGENT CLI INTERFACE
import argparse
import json
from market_agent import MarketDataAgent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()

class MarketDataCLI:
    def __init__(self, alpha_vantage_key: str = None):
        self.agent = MarketDataAgent(alpha_vantage_key)
    
    def display_stock_price(self, data: dict):
        """Display stock price data in a formatted table."""
        if "error" in data:
            rprint(f"[red]Error: {data['error']}[/red]")
            return
        
        table = Table(title=f"Stock Data: {data['symbol']} - {data['company_name']}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Current Price", f"${data['current_price']}")
        table.add_row("Change", f"${data['change']} ({data['change_percent']:.2f}%)")
        table.add_row("Volume", f"{data['volume']:,}")
        table.add_row("52W High", f"${data['high_52w']}")
        table.add_row("52W Low", f"${data['low_52w']}")
        table.add_row("Market Cap", f"{data['market_cap']}")
        table.add_row("P/E Ratio", f"{data['pe_ratio']}")
        
        console.print(table)
    
    def display_company_info(self, data: dict):
        """Display company information."""
        if "error" in data:
            rprint(f"[red]Error: {data['error']}[/red]")
            return
        
        info_text = f"""
[bold]{data['company_name']} ({data['symbol']})[/bold]

[cyan]Sector:[/cyan] {data['sector']}
[cyan]Industry:[/cyan] {data['industry']}
[cyan]Employees:[/cyan] {data['employees']}
[cyan]Location:[/cyan] {data['city']}, {data['country']}
[cyan]Website:[/cyan] {data['website']}

[yellow]Financial Metrics:[/yellow]
• Market Cap: {data['market_cap']}
• P/E Ratio: {data['pe_ratio']}
• PEG Ratio: {data['peg_ratio']}
• Price to Book: {data['price_to_book']}
• Debt to Equity: {data['debt_to_equity']}
• Dividend Yield: {data['dividend_yield']}

[yellow]Description:[/yellow]
{data['description'][:500]}...
        """
        
        panel = Panel(info_text, title="Company Information", border_style="blue")
        console.print(panel)
    
    def display_multiple_stocks(self, data: dict):
        """Display multiple stock data in a table."""
        table = Table(title="Multiple Stocks Overview")
        table.add_column("Symbol", style="cyan")
        table.add_column("Company", style="blue")
        table.add_column("Price", style="green")
        table.add_column("Change", style="red")
        table.add_column("Change %", style="red")
        
        for symbol, stock_data in data.items():
            if "error" not in stock_data:
                change_color = "green" if stock_data['change'] >= 0 else "red"
                table.add_row(
                    symbol,
                    stock_data['company_name'][:30] + "..." if len(stock_data['company_name']) > 30 else stock_data['company_name'],
                    f"${stock_data['current_price']}",
                    f"[{change_color}]${stock_data['change']:.2f}[/{change_color}]",
                    f"[{change_color}]{stock_data['change_percent']:.2f}%[/{change_color}]"
                )
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Market Data CLI Tool")
    parser.add_argument("--alpha-key", help="AlphaVantage API key")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Stock price command
    price_parser = subparsers.add_parser("price", help="Get stock price")
    price_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    price_parser.add_argument("--period", default="1mo", help="Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
    
    # Multiple stocks command
    multi_parser = subparsers.add_parser("multi", help="Get multiple stock prices")
    multi_parser.add_argument("symbols", nargs="+", help="Stock symbols (e.g., AAPL GOOGL MSFT)")
    
    # Company info command
    info_parser = subparsers.add_parser("info", help="Get company information")
    info_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    
    # Earnings command
    earnings_parser = subparsers.add_parser("earnings", help="Get earnings data")
    earnings_parser.add_argument("symbol", help="Stock symbol (e.g., AAPL)")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for stocks")
    search_parser.add_argument("query", help="Search query (company name or symbol)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = MarketDataCLI(args.alpha_key)
    
    if args.command == "price":
        data = cli.agent.get_stock_price(args.symbol, args.period)
        cli.display_stock_price(data)
    
    elif args.command == "multi":
        data = cli.agent.get_multiple_stocks(args.symbols)
        cli.display_multiple_stocks(data)
    
    elif args.command == "info":
        data = cli.agent.get_company_info(args.symbol)
        cli.display_company_info(data)
    
    elif args.command == "earnings":
        data = cli.agent.get_earnings_data(args.symbol)
        rprint(json.dumps(data, indent=2, default=str))
    
    elif args.command == "search":
        data = cli.agent.search_stocks(args.query)
        rprint(json.dumps(data, indent=2))

if __name__ == "__main__":
    main() 