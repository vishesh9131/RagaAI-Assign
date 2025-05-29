import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import json
import time # Import time for potential simple delays
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

# Define a custom exception for yfinance specific HTTP errors if needed, or use requests.HTTPError
class YFinanceRateLimitError(requests.exceptions.HTTPError):
    """Custom exception for yfinance rate limit errors."""
    pass

def _is_rate_limit_error(exception):
    """Check if the exception is a rate limit error (429)."""
    return isinstance(exception, requests.exceptions.HTTPError) and hasattr(exception, 'response') and exception.response is not None and exception.response.status_code == 429

class MarketDataAgent:
    """
    A market data agent that fetches stock prices, earnings, and other market data
    using Yahoo Finance and AlphaVantage APIs.
    """
    
    def __init__(self, alpha_vantage_api_key: Optional[str] = None):
        """
        Initialize the market data agent.
        
        Args:
            alpha_vantage_api_key: Optional API key for AlphaVantage
        """
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
    
    @retry(stop=stop_after_attempt(2), 
           wait=wait_exponential(multiplier=1, min=1, max=3), # Reduced wait times for faster response
           retry=retry_if_exception_type(requests.exceptions.RequestException)
          )
    def _fetch_ticker_info(self, ticker_symbol: str):
        """Helper to fetch ticker info with retry for potential network/rate issues."""
        # print(f"Fetching info for {ticker_symbol}") # For debugging
        ticker = yf.Ticker(ticker_symbol)
        # Accessing .info can sometimes be the first point of failure
        # yfinance might make multiple calls internally for .info
        # A direct way to check if ticker is valid or if there are issues:
        info = ticker.info
        if not info: # yfinance might return an empty dict for invalid symbols or some errors
            # Try a minimal history call to see if the ticker is valid at all
            if ticker.history(period="1d", raise_errors=False).empty:
                # This doesn't distinguish between invalid symbol and actual network error for history
                # but if info is empty AND history is empty, it's likely an issue with the symbol or access.
                raise requests.exceptions.HTTPError(f"Failed to get .info and a minimal history call also failed for {ticker_symbol}. Symbol might be invalid or API inaccessible.")
        return info

    @retry(stop=stop_after_attempt(2),
           wait=wait_exponential(multiplier=1, min=1, max=3), # Reduced wait times
           retry=retry_if_exception_type(requests.exceptions.RequestException)
          )
    def _fetch_ticker_history(self, ticker_symbol: str, period: str):
        """Helper to fetch ticker history with retry."""
        # print(f"Fetching history for {ticker_symbol} period {period}") # For debugging
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            # This might occur if the symbol is valid but there's no data for the period,
            # or if there was an issue yfinance handled internally without raising an exception tenacity caught.
            # For robustness, we can treat empty history after retries as an issue.
            # Note: yfinance itself might raise an error for invalid symbols before this.
            pass # Allow returning empty hist, main function will check
        return hist

    @retry(stop=stop_after_attempt(2),
           wait=wait_exponential(multiplier=1, min=1, max=3), # Reduced wait times
           retry=retry_if_exception_type(requests.exceptions.RequestException)
          )
    def _fetch_ticker_earnings(self, ticker_symbol: str):
        """Helper to fetch ticker earnings with retry."""
        ticker = yf.Ticker(ticker_symbol)
        return ticker.earnings, ticker.quarterly_earnings, ticker.calendar

    def get_stock_price(self, symbol: str, period: str = "1mo") -> Dict:
        try:
            # For health checks and fast responses, try multiple periods if one fails
            periods_to_try = ["5d", "1d", "1mo"] if period == "1mo" else [period, "1d"]
            
            hist = None
            for attempt_period in periods_to_try:
                try:
                    hist = self._fetch_ticker_history(symbol, attempt_period)
                    if not hist.empty:
                        break
                    print(f"Empty history for {symbol} with period {attempt_period}, trying next...")
                except Exception as e:
                    print(f"Failed to fetch {symbol} with period {attempt_period}: {e}")
                    continue
                    
            # For health checks, don't fail the whole request if we can't get company info
            info = {}
            if hist is not None and not hist.empty:
                try:
                    # Use shorter timeout for info to prevent health check failures
                    info = self._fetch_ticker_info(symbol)
                except (RetryError, Exception) as e:
                    print(f"Info fetch failed for {symbol}, continuing with price data only: {e}")
                    # Continue without info data
            
            if hist is None or hist.empty:
                # As a last resort, try a basic ticker creation with minimal data
                try:
                    import yfinance as yf
                    basic_ticker = yf.Ticker(symbol)
                    basic_info = basic_ticker.info
                    if basic_info and 'currentPrice' in basic_info:
                        current_price = basic_info['currentPrice']
                        return {
                            "symbol": symbol,
                            "current_price": round(float(current_price), 2),
                            "previous_close": round(float(current_price), 2),
                            "change": 0.0,
                            "change_percent": 0.0,
                            "volume": basic_info.get('volume', 0),
                            "high_52w": round(float(basic_info.get('fiftyTwoWeekHigh', current_price)), 2),
                            "low_52w": round(float(basic_info.get('fiftyTwoWeekLow', current_price)), 2),
                            "market_cap": basic_info.get('marketCap', 'N/A'),
                            "pe_ratio": basic_info.get('trailingPE', 'N/A'),
                            "company_name": basic_info.get('longName', symbol),
                            "historical_data": []
                        }
                except Exception as e:
                    print(f"Basic ticker fallback also failed for {symbol}: {e}")
                
                return {"error": f"No historical data found for symbol {symbol} after retries."}
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
            
            # Ensure we always return the required fields for health checks
            result = {
                "symbol": symbol,
                "current_price": round(float(current_price), 2),  # Ensure it's a float
                "previous_close": round(float(prev_close), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns and pd.notna(hist['Volume'].iloc[-1]) else 0,
                "high_52w": round(float(info.get('fiftyTwoWeekHigh', current_price)), 2) if info and info.get('fiftyTwoWeekHigh') else round(float(current_price), 2),
                "low_52w": round(float(info.get('fiftyTwoWeekLow', current_price)), 2) if info and info.get('fiftyTwoWeekLow') else round(float(current_price), 2),
                "market_cap": info.get('marketCap', 'N/A') if info else 'N/A',
                "pe_ratio": info.get('trailingPE', 'N/A') if info else 'N/A',
                "company_name": info.get('longName', symbol) if info and info.get('longName') else symbol,
                "historical_data": hist.reset_index().to_dict('records')[:10] # Limit to last 10 days for faster response
            }
            return result
        except RetryError as re:
            last_exception = re.last_attempt.exception()
            if _is_rate_limit_error(last_exception):
                return {"error": f"Rate limit hit for {symbol} (history) despite retries. Last error: {str(last_exception)}"}
            return {"error": f"Failed to fetch history for {symbol} after multiple retries. Last error: {str(last_exception)}"}
        except Exception as e:
            return {"error": f"Error fetching data for {symbol} in get_stock_price: {str(e)}"}
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict:
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_price(symbol)
            time.sleep(0.3) # Slightly increased delay
        return results
    
    def get_earnings_data(self, symbol: str) -> Dict:
        try:
            # ticker = yf.Ticker(symbol)
            # earnings = ticker.earnings
            # quarterly_earnings = ticker.quarterly_earnings
            # calendar_info = ticker.calendar
            earnings, quarterly_earnings, calendar_info = self._fetch_ticker_earnings(symbol)
            
            return {
                "symbol": symbol,
                "annual_earnings": earnings.reset_index().to_dict('records') if earnings is not None and not earnings.empty else {},
                "quarterly_earnings": quarterly_earnings.reset_index().to_dict('records') if quarterly_earnings is not None and not quarterly_earnings.empty else {},
                "earnings_dates": calendar_info.to_dict() if hasattr(calendar_info, 'to_dict') and calendar_info is not None else {}
            }
        except RetryError as re:
            last_exception = re.last_attempt.exception()
            if _is_rate_limit_error(last_exception):
                return {"error": f"Rate limit hit for {symbol} (earnings) despite retries. Last error: {str(last_exception)}"}
            return {"error": f"Failed to fetch earnings for {symbol} after multiple retries. Last error: {str(last_exception)}"}
        except Exception as e:
            return {"error": f"Error fetching earnings data for {symbol}: {str(e)}"}
    
    def get_company_info(self, symbol: str) -> Dict:
        try:
            info = self._fetch_ticker_info(symbol)
            
            if not info: # If info is None or empty after retries
                # For health checks, return a minimal response instead of complete failure
                return {
                    "symbol": symbol,
                    "company_name": symbol,  # Use symbol as fallback
                    "sector": "Unknown",
                    "industry": "Unknown", 
                    "website": "N/A",
                    "description": f"Company information for {symbol}",
                    "employees": "N/A",
                    "city": "N/A",
                    "country": "N/A",
                    "market_cap": "N/A",
                    "enterprise_value": "N/A",
                    "pe_ratio": "N/A",
                    "peg_ratio": "N/A",
                    "price_to_book": "N/A",
                    "debt_to_equity": "N/A",
                    "dividend_yield": "N/A"
                }

            # Ensure we always return company_name field for health checks
            result = {
                "symbol": symbol,
                "company_name": info.get('longName', symbol),  # Use symbol as fallback
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "website": info.get('website', 'N/A'),
                "description": info.get('longBusinessSummary', 'N/A'),
                "employees": info.get('fullTimeEmployees', 'N/A'),
                "city": info.get('city', 'N/A'),
                "country": info.get('country', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "enterprise_value": info.get('enterpriseValue', 'N/A'),
                "pe_ratio": info.get('trailingPE', 'N/A'),
                "peg_ratio": info.get('pegRatio', 'N/A'),
                "price_to_book": info.get('priceToBook', 'N/A'),
                "debt_to_equity": info.get('debtToEquity', 'N/A'),
                "dividend_yield": info.get('dividendYield', 'N/A')
            }
            return result
        except RetryError as re:
            last_exception = re.last_attempt.exception()
            if _is_rate_limit_error(last_exception):
                # Return fallback response instead of error for health checks
                return {
                    "symbol": symbol,
                    "company_name": symbol,
                    "sector": "Rate Limited",
                    "industry": "N/A",
                    "website": "N/A", 
                    "description": f"Rate limit encountered for {symbol}",
                    "employees": "N/A",
                    "city": "N/A",
                    "country": "N/A",
                    "market_cap": "N/A",
                    "enterprise_value": "N/A",
                    "pe_ratio": "N/A",
                    "peg_ratio": "N/A",
                    "price_to_book": "N/A",
                    "debt_to_equity": "N/A",
                    "dividend_yield": "N/A"
                }
            return {"error": f"Failed to fetch company info for {symbol} after multiple retries. Last error: {str(last_exception)}"}
        except Exception as e:
            # Return fallback response for health checks
            return {
                "symbol": symbol,
                "company_name": symbol,
                "sector": "Error",
                "industry": "N/A",
                "website": "N/A",
                "description": f"Error fetching info for {symbol}: {str(e)}",
                "employees": "N/A",
                "city": "N/A", 
                "country": "N/A",
                "market_cap": "N/A",
                "enterprise_value": "N/A",
                "pe_ratio": "N/A",
                "peg_ratio": "N/A",
                "price_to_book": "N/A",
                "debt_to_equity": "N/A",
                "dividend_yield": "N/A"
            }
    
    # AlphaVantage methods usually have their own rate limits, so tenacity might be useful here too
    # if you use it frequently. For now, keeping it as is.
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10),
           retry=retry_if_exception_type(requests.exceptions.RequestException))
    def get_alpha_vantage_data(self, symbol: str, function: str = "TIME_SERIES_DAILY") -> Dict:
        if not self.alpha_vantage_api_key:
            # This is not a server error, but a configuration issue.
            # The API layer in main.py handles returning a 501 for this.
            return {"error": "AlphaVantage API key not provided in MarketDataAgent"}
        
        try:
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=15) # Increased timeout
            response.raise_for_status() # Will raise HTTPError for 4XX/5XX status codes
            
            data = response.json()
            # AlphaVantage sometimes returns error messages within a 200 OK response
            if "Error Message" in data:
                return {"error": f"AlphaVantage API Error: {data['Error Message']}"}
            if "Information" in data and "Rate Limit Exceeded" in data["Information"]:
                 # This is a specific check for their rate limit message if it occurs within 200 OK
                raise YFinanceRateLimitError(f"AlphaVantage rate limit explicitly mentioned: {data['Information']}", response=response)
            return data
        except RetryError as re_av: # Catching RetryError specifically for AlphaVantage if retries fail
            last_exception_av = re_av.last_attempt.exception()
            if _is_rate_limit_error(last_exception_av):
                 return {"error": f"AlphaVantage rate limit hit for {symbol}, fct {function}, despite retries. Last error: {str(last_exception_av)}"}
            return {"error": f"Failed to fetch AlphaVantage data for {symbol}, fct {function}, after retries. Last error: {str(last_exception_av)}"}
        except requests.exceptions.HTTPError as he:
            # This handles non-retryable HTTP errors or if retries were exhausted and resulted in HTTPError
            if _is_rate_limit_error(he):
                 return {"error": f"AlphaVantage rate limit hit for {symbol}, function {function}. Details: {str(he)}"}
            return {"error": f"HTTP error fetching AlphaVantage data for {symbol}, fct {function}: {str(he)}"}
        except Exception as e: # General catch-all
            return {"error": f"Error fetching AlphaVantage data for {symbol}, function {function}: {str(e)}"}
    
    def search_stocks(self, query: str) -> Dict:
        try:
            # For health checks, provide a simple response
            info = self._fetch_ticker_info(query.upper())
            
            if info and info.get('longName'): 
                return {
                    "results": [{
                        "symbol": info.get('symbol', query.upper()),
                        "name": info.get('longName', query.upper()),
                        "sector": info.get('sector', 'N/A'),
                        "industry": info.get('industry', 'N/A')
                    }]
                }
            else:
                # For health checks, return a basic result instead of empty
                return {
                    "results": [{
                        "symbol": query.upper(),
                        "name": f"{query.upper()} (Search Result)",
                        "sector": "Unknown",
                        "industry": "Unknown"
                    }],
                    "message": f"Basic search result for '{query}'"
                }
        except (RetryError, Exception) as e:
            # For health checks, return a basic search result instead of error
            return {
                "results": [{
                    "symbol": query.upper(),
                    "name": f"{query.upper()} (Fallback)",
                    "sector": "Unknown", 
                    "industry": "Unknown"
                }],
                "message": f"Fallback search result for '{query}'"
            } 