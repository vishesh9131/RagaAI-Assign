import argparse
import pandas as pd
from rich.console import Console
from rich.table import Table
from analysis_agent import AnalysisAgent

console = Console()
agent = AnalysisAgent()

def display_df(df, title="Results"):
    if isinstance(df, pd.DataFrame):
        table = Table(title=title)
        for col in df.columns:
            table.add_column(col)
        for _, row in df.iterrows():
            table.add_row(*[str(x) for x in row.values])
        console.print(table)
    else:
        console.print(df)

def display_dict(data: dict, title="Result"):
    table = Table(title=title)
    table.add_column("Metric")
    table.add_column("Value")
    for key, value in data.items():
        table.add_row(str(key).replace("_", " ").title(), str(value))
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="CLI for the Analysis Agent.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Investment by region/sector command
    invest_parser = subparsers.add_parser("investment", help="Calculate total investment by region and sector.")
    invest_parser.add_argument("region", type=str, help="Region name (e.g., 'Asia', 'US')")
    invest_parser.add_argument("sector", type=str, help="Sector name (e.g., 'Tech', 'Auto')")
    invest_parser.add_argument("--data_type", type=str, default="today", choices=['today', 'yesterday'], help="Data snapshot to use (today or yesterday)")

    # Portfolio value change command
    change_parser = subparsers.add_parser("portfolio_change", help="Calculate portfolio value change from yesterday to today.")

    # Sentiment trends command
    sentiment_parser = subparsers.add_parser("sentiment", help="Analyze sentiment of news headlines.")
    sentiment_parser.add_argument("--texts", type=str, nargs="*", help="Optional list of texts to analyze instead of default headlines.")

    # Stock price comparison command
    price_comp_parser = subparsers.add_parser("price_compare", help="Compare yesterday and today stock prices.")
    price_comp_parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g., 'AAPL')")

    args = parser.parse_args()

    if args.command == "investment":
        try:
            total_investment = agent.get_investment_by_region_sector(args.region, args.sector, args.data_type)
            console.print(f"Total investment in {args.region.upper()} {args.sector.upper()} ({args.data_type.capitalize()}): ${total_investment:.2f}")
        except ValueError as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
    
    elif args.command == "portfolio_change":
        change_data = agent.get_portfolio_value_change()
        display_dict(change_data, title="Portfolio Value Change")

    elif args.command == "sentiment":
        custom_texts = args.texts if args.texts else None
        sentiments_df = agent.get_sentiment_trends(texts=custom_texts)
        display_df(sentiments_df, title="Sentiment Analysis")

    elif args.command == "price_compare":
        price_data = agent.compare_stock_prices(args.ticker)
        if "error" in price_data:
            console.print(f"[bold red]Error: {price_data['error']}[/bold red]")
        else:
            display_dict(price_data, title=f"{args.ticker.upper()} Price Comparison")

if __name__ == "__main__":
    main() 