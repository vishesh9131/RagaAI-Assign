#!/usr/bin/env python3
"""
Comprehensive Health Checker for Multi-Agent Financial Data System

Tests all CLI commands and API endpoints for:
- Analysis Agent
- Language Agent  
- Market Agent
- Retriever Agent
- Scraping Agent
- Voice Agent
"""

import subprocess
import requests
import json
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import print as rprint

console = Console()

class HealthChecker:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.cli_results = {}
        self.api_results = {}
        
    def check_api_server(self) -> bool:
        """Check if the API server is running"""
        try:
            response = requests.get(f"{self.api_base_url}/docs", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    # =============== CLI HEALTH CHECKS ===============

    def test_analysis_cli(self) -> Dict[str, bool]:
        """Test Analysis Agent CLI commands"""
        results = {}
        
        # Test investment command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python analysis_cli.py investment Asia Tech --data_type today"
            ], capture_output=True, text=True, timeout=30)
            results["investment"] = result.returncode == 0 and "Total investment" in result.stdout
        except Exception as e:
            results["investment"] = False
            
        # Test portfolio_change command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python analysis_cli.py portfolio_change"
            ], capture_output=True, text=True, timeout=30)
            results["portfolio_change"] = result.returncode == 0 and "Portfolio Value Change" in result.stdout
        except Exception:
            results["portfolio_change"] = False
            
        # Test sentiment command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python analysis_cli.py sentiment"
            ], capture_output=True, text=True, timeout=30)
            results["sentiment"] = result.returncode == 0 and "Sentiment Analysis" in result.stdout
        except Exception:
            results["sentiment"] = False
            
        # Test price_compare command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python analysis_cli.py price_compare AAPL"
            ], capture_output=True, text=True, timeout=30)
            results["price_compare"] = result.returncode == 0 and "Price Comparison" in result.stdout
        except Exception:
            results["price_compare"] = False
            
        return results

    def test_language_cli(self) -> Dict[str, bool]:
        """Test Language Agent CLI commands"""
        results = {}
        
        # Test summarize command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python language_cli.py summarize 'This is a test text for summarization. It contains multiple sentences to test the summarization functionality.'"
            ], capture_output=True, text=True, timeout=30)
            results["summarize"] = result.returncode == 0 and "Summary:" in result.stdout
        except Exception:
            results["summarize"] = False
            
        # Test explain command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python language_cli.py explain 'Machine learning is a subset of artificial intelligence.'"
            ], capture_output=True, text=True, timeout=30)
            results["explain"] = result.returncode == 0 and "Explanation:" in result.stdout
        except Exception:
            results["explain"] = False
            
        return results

    def test_market_cli(self) -> Dict[str, bool]:
        """Test Market Agent CLI commands"""
        results = {}
        
        # Test price command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python cli_interface.py price AAPL"
            ], capture_output=True, text=True, timeout=30)
            results["price"] = result.returncode == 0 and ("Current Price" in result.stdout or "Stock Data" in result.stdout)
        except Exception:
            results["price"] = False
            
        # Test info command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python cli_interface.py info AAPL"
            ], capture_output=True, text=True, timeout=30)
            results["info"] = result.returncode == 0 and ("Company Information" in result.stdout or "AAPL" in result.stdout)
        except Exception:
            results["info"] = False
            
        # Test search command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python cli_interface.py search Apple"
            ], capture_output=True, text=True, timeout=30)
            results["search"] = result.returncode == 0
        except Exception:
            results["search"] = False
            
        return results

    def test_retriever_cli(self) -> Dict[str, bool]:
        """Test Retriever Agent CLI commands"""
        results = {}
        
        # Test add command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python retriever_cli.py add 'This is a test document for the retriever agent health check.' --metadatas '[{\"source\": \"health_check\"}]'"
            ], capture_output=True, text=True, timeout=30)
            results["add"] = result.returncode == 0 and "Successfully added" in result.stdout
        except Exception:
            results["add"] = False
            
        # Test search command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python retriever_cli.py search 'test document' -k 3"
            ], capture_output=True, text=True, timeout=30)
            results["search"] = result.returncode == 0
        except Exception:
            results["search"] = False
            
        # Test info command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python retriever_cli.py info"
            ], capture_output=True, text=True, timeout=30)
            results["info"] = result.returncode == 0 and "Store Information" in result.stdout
        except Exception:
            results["info"] = False
            
        return results

    def test_scraping_cli(self) -> Dict[str, bool]:
        """Test Scraping Agent CLI commands"""
        results = {}
        
        # Test fetch-html command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python scraping_cli.py fetch-html https://httpbin.org/html"
            ], capture_output=True, text=True, timeout=30)
            results["fetch_html"] = result.returncode == 0 and "HTML Content" in result.stdout
        except Exception:
            results["fetch_html"] = False
            
        # Test extract-text command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python scraping_cli.py extract-text https://httpbin.org/html"
            ], capture_output=True, text=True, timeout=30)
            results["extract_text"] = result.returncode == 0
        except Exception:
            results["extract_text"] = False
            
        return results

    def test_voice_cli(self) -> Dict[str, bool]:
        """Test Voice Agent CLI commands"""
        results = {}
        
        # Test tts command
        try:
            result = subprocess.run([
                "bash", "-c", "source market_env/bin/activate && python voice_cli.py tts 'Health check test' --output /tmp/health_check_voice.wav"
            ], capture_output=True, text=True, timeout=30)
            results["tts"] = result.returncode == 0 and "Audio saved to" in result.stdout
            # Clean up test file
            Path("/tmp/health_check_voice.wav").unlink(missing_ok=True)
        except Exception:
            results["tts"] = False
            
        return results

    # =============== API HEALTH CHECKS ===============

    def test_analysis_api(self) -> Dict[str, bool]:
        """Test Analysis Agent API endpoints"""
        results = {}
        
        # Test investment by region/sector
        try:
            response = requests.post(f"{self.api_base_url}/analysis/investment_by_region_sector", 
                json={"region_name": "Asia", "sector_name": "Tech", "data_type": "today"}, 
                timeout=30)
            results["investment_api"] = response.status_code == 200 and "total_investment" in response.text
        except Exception:
            results["investment_api"] = False
            
        # Test portfolio change
        try:
            response = requests.get(f"{self.api_base_url}/analysis/portfolio_change", timeout=30)
            results["portfolio_change_api"] = response.status_code == 200 and "yesterday_value" in response.text
        except Exception:
            results["portfolio_change_api"] = False
            
        # Test sentiment analysis
        try:
            response = requests.post(f"{self.api_base_url}/analysis/sentiment_trends",
                json={"texts": ["Test positive sentiment", "Test negative sentiment"]}, 
                timeout=30)
            results["sentiment_api"] = response.status_code == 200 and "sentiments" in response.text
        except Exception:
            results["sentiment_api"] = False
            
        # Test stock price comparison
        try:
            response = requests.get(f"{self.api_base_url}/analysis/stock_price_comparison?ticker=AAPL", timeout=30)
            results["price_compare_api"] = response.status_code == 200
        except Exception:
            results["price_compare_api"] = False
            
        return results

    def test_language_api(self) -> Dict[str, bool]:
        """Test Language Agent API endpoints"""
        results = {}
        
        # Test summarize
        try:
            response = requests.post(f"{self.api_base_url}/language/summarize",
                json={"text": "This is a test text for summarization via API. It contains multiple sentences.", "max_words": 50},
                timeout=30)
            results["summarize_api"] = response.status_code == 200 and "summary" in response.text
        except Exception:
            results["summarize_api"] = False
            
        # Test explain
        try:
            response = requests.post(f"{self.api_base_url}/language/explain",
                json={"text": "Machine learning is a subset of artificial intelligence.", "audience": "beginner"},
                timeout=30)
            results["explain_api"] = response.status_code == 200 and "explanation" in response.text
        except Exception:
            results["explain_api"] = False
            
        return results

    def test_market_api(self) -> Dict[str, bool]:
        """Test Market Agent API endpoints"""
        results = {}
        
        # Test stock price
        try:
            response = requests.get(f"{self.api_base_url}/market/stock/AAPL/price", timeout=30)
            results["price_api"] = response.status_code == 200 and "current_price" in response.text
        except Exception:
            results["price_api"] = False
            
        # Test company info
        try:
            response = requests.get(f"{self.api_base_url}/market/stock/AAPL/info", timeout=30)
            results["info_api"] = response.status_code == 200 and "company_name" in response.text
        except Exception:
            results["info_api"] = False
            
        # Test search
        try:
            response = requests.get(f"{self.api_base_url}/market/search/Apple", timeout=30)
            results["search_api"] = response.status_code == 200
        except Exception:
            results["search_api"] = False
            
        return results

    def test_retriever_api(self) -> Dict[str, bool]:
        """Test Retriever Agent API endpoints"""
        results = {}
        
        # Test add texts
        try:
            response = requests.post(f"{self.api_base_url}/retriever/add",
                json={"texts": ["Health check test document for API"], "metadatas": [{"source": "api_health_check"}]},
                timeout=30)
            results["add_api"] = response.status_code == 200 and "Successfully added" in response.text
        except Exception:
            results["add_api"] = False
            
        # Test search
        try:
            response = requests.post(f"{self.api_base_url}/retriever/search",
                json={"query": "health check test", "k": 3},
                timeout=30)
            results["search_api"] = response.status_code == 200
        except Exception:
            results["search_api"] = False
            
        # Test info
        try:
            response = requests.get(f"{self.api_base_url}/retriever/info", timeout=30)
            results["info_api"] = response.status_code == 200 and "total_document_chunks" in response.text
        except Exception:
            results["info_api"] = False
            
        return results

    def test_scraping_api(self) -> Dict[str, bool]:
        """Test Scraping Agent API endpoints"""
        results = {}
        
        # Test fetch HTML
        try:
            response = requests.post(f"{self.api_base_url}/scrape/html",
                json={"url": "https://httpbin.org/html"},
                timeout=30)
            results["fetch_html_api"] = response.status_code == 200 and "html_sample" in response.text
        except Exception:
            results["fetch_html_api"] = False
            
        # Test extract text
        try:
            response = requests.post(f"{self.api_base_url}/scrape/text",
                json={"url": "https://httpbin.org/html"},
                timeout=30)
            results["extract_text_api"] = response.status_code == 200
        except Exception:
            results["extract_text_api"] = False
            
        return results

    def test_voice_api(self) -> Dict[str, bool]:
        """Test Voice Agent API endpoints"""
        results = {}
        
        # Test TTS
        try:
            response = requests.post(f"{self.api_base_url}/voice/tts",
                json={"text": "API health check test", "filename": "/tmp/api_health_check.wav"},
                timeout=30)
            results["tts_api"] = response.status_code == 200 and "wav_path" in response.text
            # Clean up test file
            Path("/tmp/api_health_check.wav").unlink(missing_ok=True)
        except Exception:
            results["tts_api"] = False
            
        return results

    # =============== MAIN TESTING METHODS ===============

    def run_cli_tests(self) -> Dict[str, Dict[str, bool]]:
        """Run all CLI tests"""
        rprint("[bold blue]🔧 Running CLI Health Checks...[/bold blue]")
        
        with Progress() as progress:
            task = progress.add_task("Testing CLI agents...", total=6)
            
            # Analysis Agent
            progress.update(task, description="Testing Analysis CLI...")
            self.cli_results["analysis"] = self.test_analysis_cli()
            progress.advance(task)
            
            # Language Agent
            progress.update(task, description="Testing Language CLI...")
            self.cli_results["language"] = self.test_language_cli()
            progress.advance(task)
            
            # Market Agent
            progress.update(task, description="Testing Market CLI...")
            self.cli_results["market"] = self.test_market_cli()
            progress.advance(task)
            
            # Retriever Agent
            progress.update(task, description="Testing Retriever CLI...")
            self.cli_results["retriever"] = self.test_retriever_cli()
            progress.advance(task)
            
            # Scraping Agent
            progress.update(task, description="Testing Scraping CLI...")
            self.cli_results["scraping"] = self.test_scraping_cli()
            progress.advance(task)
            
            # Voice Agent
            progress.update(task, description="Testing Voice CLI...")
            self.cli_results["voice"] = self.test_voice_cli()
            progress.advance(task)
            
        return self.cli_results

    def run_api_tests(self) -> Dict[str, Dict[str, bool]]:
        """Run all API tests"""
        if not self.check_api_server():
            rprint(f"[bold red]❌ API Server not running at {self.api_base_url}[/bold red]")
            return {}
            
        rprint("[bold blue]🌐 Running API Health Checks...[/bold blue]")
        
        with Progress() as progress:
            task = progress.add_task("Testing API endpoints...", total=6)
            
            # Analysis Agent
            progress.update(task, description="Testing Analysis API...")
            self.api_results["analysis"] = self.test_analysis_api()
            progress.advance(task)
            
            # Language Agent
            progress.update(task, description="Testing Language API...")
            self.api_results["language"] = self.test_language_api()
            progress.advance(task)
            
            # Market Agent
            progress.update(task, description="Testing Market API...")
            self.api_results["market"] = self.test_market_api()
            progress.advance(task)
            
            # Retriever Agent
            progress.update(task, description="Testing Retriever API...")
            self.api_results["retriever"] = self.test_retriever_api()
            progress.advance(task)
            
            # Scraping Agent
            progress.update(task, description="Testing Scraping API...")
            self.api_results["scraping"] = self.test_scraping_api()
            progress.advance(task)
            
            # Voice Agent
            progress.update(task, description="Testing Voice API...")
            self.api_results["voice"] = self.test_voice_api()
            progress.advance(task)
            
        return self.api_results

    def display_results(self):
        """Display health check results in formatted tables"""
        
        # CLI Results
        if self.cli_results:
            rprint("\n[bold cyan]📋 CLI Health Check Results[/bold cyan]")
            cli_table = Table(title="CLI Commands Status")
            cli_table.add_column("Agent", style="cyan")
            cli_table.add_column("Command", style="blue")
            cli_table.add_column("Status", style="green")
            
            for agent, commands in self.cli_results.items():
                for command, status in commands.items():
                    status_icon = "✅ PASS" if status else "❌ FAIL"
                    status_style = "green" if status else "red"
                    cli_table.add_row(agent.capitalize(), command, f"[{status_style}]{status_icon}[/{status_style}]")
            
            console.print(cli_table)
        
        # API Results
        if self.api_results:
            rprint("\n[bold cyan]🌐 API Health Check Results[/bold cyan]")
            api_table = Table(title="API Endpoints Status")
            api_table.add_column("Agent", style="cyan")
            api_table.add_column("Endpoint", style="blue")
            api_table.add_column("Status", style="green")
            
            for agent, endpoints in self.api_results.items():
                for endpoint, status in endpoints.items():
                    status_icon = "✅ PASS" if status else "❌ FAIL"
                    status_style = "green" if status else "red"
                    api_table.add_row(agent.capitalize(), endpoint.replace("_api", ""), f"[{status_style}]{status_icon}[/{status_style}]")
            
            console.print(api_table)
        
        # Summary
        self.display_summary()

    def display_summary(self):
        """Display overall health summary"""
        cli_total = sum(len(commands) for commands in self.cli_results.values())
        cli_passed = sum(sum(commands.values()) for commands in self.cli_results.values())
        
        api_total = sum(len(endpoints) for endpoints in self.api_results.values())
        api_passed = sum(sum(endpoints.values()) for endpoints in self.api_results.values())
        
        total_tests = cli_total + api_total
        total_passed = cli_passed + api_passed
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            
            summary_text = f"""
[bold]Overall Health Check Summary[/bold]

CLI Tests: {cli_passed}/{cli_total} passed
API Tests: {api_passed}/{api_total} passed
Total: {total_passed}/{total_tests} passed ({success_rate:.1f}%)

Status: {"🎉 HEALTHY" if success_rate >= 90 else "⚠️  ISSUES DETECTED" if success_rate >= 75 else "🚨 CRITICAL"}
            """
            
            color = "green" if success_rate >= 90 else "yellow" if success_rate >= 75 else "red"
            rprint(Panel(summary_text, border_style=color))

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent System Health Checker")
    parser.add_argument("--mode", choices=["cli", "api", "both"], default="both",
                        help="Test mode: cli, api, or both")
    parser.add_argument("--api-url", default="http://localhost:8000",
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")
    
    args = parser.parse_args()
    
    checker = HealthChecker(api_base_url=args.api_url)
    
    rprint("[bold green]🔍 Multi-Agent System Health Checker[/bold green]")
    rprint(f"Mode: {args.mode.upper()}")
    rprint(f"API URL: {args.api_url}")
    rprint()
    
    try:
        if args.mode in ["cli", "both"]:
            checker.run_cli_tests()
            
        if args.mode in ["api", "both"]:
            checker.run_api_tests()
            
        checker.display_results()
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Health check interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        rprint(f"\n[red]Error during health check: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 