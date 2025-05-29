import pandas as pd
import numpy as np
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import ssl

# Ensure SSL download works even with self-signed / missing root certs
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download vader_lexicon if not already present
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    try:
        nltk.download('vader_lexicon', quiet=True)
    except Exception as e:
        # If download fails (e.g., no internet / SSL issues), inform user but continue.
        print("[AnalysisAgent] Warning: Failed to download 'vader_lexicon'. Sentiment analysis will be disabled.")
        print(f"Download error: {e}")

class AnalysisAgent:
    def __init__(self):
        # Initialize sentiment analyzer if lexicon is available
        try:
            self.analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            # Lexicon still missing – fallback to dummy analyzer that returns neutral scores
            print("[AnalysisAgent] 'vader_lexicon' not available. Using neutral sentiment fallback.")
            class _NeutralAnalyzer:
                def polarity_scores(self, text):
                    return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
            self.analyzer = _NeutralAnalyzer()
        # Placeholder for data - in a real scenario, this would be fetched
        # from MarketDataAgent, ScrapingAgent, or RetrieverAgent
        self.portfolio_data = {
            'yesterday': pd.DataFrame({
                'Ticker': ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA-AS', 'BABA-HK'],
                'Region': ['US', 'US', 'US', 'US', 'US', 'Asia', 'Asia'],
                'Sector': ['Tech', 'Tech', 'Tech', 'E-commerce', 'Auto', 'Tech', 'E-commerce'],
                'InvestedValue': [15000, 20000, 18000, 12000, 8000, 10000, 7000],
                'Price': [170.0, 330.0, 2500.0, 120.0, 250.0, 450.0, 90.0]
            }),
            'today': pd.DataFrame({
                'Ticker': ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA-AS', 'BABA-HK'],
                'Region': ['US', 'US', 'US', 'US', 'US', 'Asia', 'Asia'],
                'Sector': ['Tech', 'Tech', 'Tech', 'E-commerce', 'Auto', 'Tech', 'E-commerce'],
                'InvestedValue': [15500, 20500, 17500, 12200, 8100, 10500, 6800],
                'Price': [172.0, 335.0, 2450.0, 122.0, 255.0, 460.0, 88.0]
            })
        }
        self.news_headlines = [
            "Tech stocks soar on positive earnings reports.",
            "New regulations may impact Asian markets.",
            "Global chip shortage continues to affect auto industry.",
            "E-commerce giants see record sales.",
            "Mixed feelings on new EV model from Tesla."
        ]

    def get_investment_by_region_sector(self, region_name: str, sector_name: str, data_type: str = 'today') -> float:
        """Calculates total investment in a specific region and sector."""
        if data_type not in self.portfolio_data:
            raise ValueError("Invalid data_type. Choose 'today' or 'yesterday'.")
        
        data = self.portfolio_data[data_type]
        filtered_data = data[(data['Region'].str.lower() == region_name.lower()) & 
                             (data['Sector'].str.lower() == sector_name.lower())]
        return filtered_data['InvestedValue'].sum()

    def get_portfolio_value_change(self) -> dict:
        """Calculates the change in total portfolio value from yesterday to today."""
        yesterday_value = self.portfolio_data['yesterday']['InvestedValue'].sum()
        today_value = self.portfolio_data['today']['InvestedValue'].sum()
        change = today_value - yesterday_value
        percentage_change = (change / yesterday_value) * 100 if yesterday_value else 0
        return {
            "yesterday_value": yesterday_value,
            "today_value": today_value,
            "change": change,
            "percentage_change": round(percentage_change, 2)
        }

    def get_sentiment_trends(self, texts: list = None) -> pd.DataFrame:
        """Analyzes sentiment of a list of texts (e.g., news headlines)."""
        if texts is None:
            texts = self.news_headlines
        
        sentiments = []
        for text in texts:
            vs = self.analyzer.polarity_scores(text)
            sentiments.append({
                'text': text,
                'positive': vs['pos'],
                'negative': vs['neg'],
                'neutral': vs['neu'],
                'compound': vs['compound']
            })
        return pd.DataFrame(sentiments)

    def compare_stock_prices(self, ticker: str) -> dict:
        """Compares yesterday's and today's price for a given stock ticker."""
        yesterday_price = self.portfolio_data['yesterday']
        today_price = self.portfolio_data['today']

        yesterday_stock = yesterday_price[yesterday_price['Ticker'].str.lower() == ticker.lower()]
        today_stock = today_price[today_price['Ticker'].str.lower() == ticker.lower()]

        if yesterday_stock.empty or today_stock.empty:
            return {"error": f"Ticker {ticker} not found in one or both datasets."}

        price_y = yesterday_stock['Price'].iloc[0]
        price_t = today_stock['Price'].iloc[0]
        change = price_t - price_y
        percentage_change = (change / price_y) * 100 if price_y else 0
        
        return {
            "ticker": ticker,
            "yesterday_price": price_y,
            "today_price": price_t,
            "price_change": change,
            "percentage_price_change": round(percentage_change, 2)
        }

    def identify_market_trends(self, sector: str, region: str, time_horizon: str = "1 week") -> str:
        """Identifies market trends for a specific sector and region over a given time horizon."""
        try:
            # Filter data for the specified sector and region
            yesterday_data = self.portfolio_data['yesterday']
            today_data = self.portfolio_data['today']
            
            yesterday_filtered = yesterday_data[
                (yesterday_data['Region'].str.lower() == region.lower()) & 
                (yesterday_data['Sector'].str.lower() == sector.lower())
            ]
            today_filtered = today_data[
                (today_data['Region'].str.lower() == region.lower()) & 
                (today_data['Sector'].str.lower() == sector.lower())
            ]
            
            if yesterday_filtered.empty or today_filtered.empty:
                return f"No data available for {sector} sector in {region} region."
            
            # Calculate overall performance
            yesterday_total = yesterday_filtered['InvestedValue'].sum()
            today_total = today_filtered['InvestedValue'].sum()
            overall_change = ((today_total - yesterday_total) / yesterday_total) * 100 if yesterday_total > 0 else 0
            
            # Analyze individual stocks performance
            stock_performances = []
            for ticker in yesterday_filtered['Ticker']:
                yesterday_stock = yesterday_filtered[yesterday_filtered['Ticker'] == ticker]
                today_stock = today_filtered[today_filtered['Ticker'] == ticker]
                
                if not yesterday_stock.empty and not today_stock.empty:
                    yesterday_value = yesterday_stock['InvestedValue'].iloc[0]
                    today_value = today_stock['InvestedValue'].iloc[0]
                    change_pct = ((today_value - yesterday_value) / yesterday_value) * 100 if yesterday_value > 0 else 0
                    stock_performances.append({
                        'ticker': ticker,
                        'change_pct': change_pct
                    })
            
            # Generate trend analysis
            if overall_change > 2:
                trend_direction = "strongly positive"
            elif overall_change > 0:
                trend_direction = "positive"
            elif overall_change > -2:
                trend_direction = "neutral"
            else:
                trend_direction = "negative"
            
            # Find best and worst performers
            if stock_performances:
                best_performer = max(stock_performances, key=lambda x: x['change_pct'])
                worst_performer = min(stock_performances, key=lambda x: x['change_pct'])
                
                trend_analysis = f"""Market Trends Analysis for {sector} sector in {region} region ({time_horizon}):

Overall Performance: {trend_direction} ({overall_change:+.2f}%)
Total Portfolio Value: ${yesterday_total:,.0f} → ${today_total:,.0f}

Stock Performance:
• Best Performer: {best_performer['ticker']} ({best_performer['change_pct']:+.2f}%)
• Worst Performer: {worst_performer['ticker']} ({worst_performer['change_pct']:+.2f}%)

Market Sentiment: Based on current data, the {sector} sector in {region} shows {trend_direction} momentum. 
This analysis covers {len(stock_performances)} stocks in the portfolio for the specified region and sector."""
            
            else:
                trend_analysis = f"Insufficient data to perform detailed trend analysis for {sector} sector in {region} region."
            
            return trend_analysis
            
        except Exception as e:
            return f"Error analyzing market trends for {sector} in {region}: {str(e)}"

if __name__ == '__main__':
    agent = AnalysisAgent()

    # Example Usage:
    asia_tech_investment_today = agent.get_investment_by_region_sector('asia', 'tech', 'today')
    print(f"Total investment in Asia Tech (Today): ${asia_tech_investment_today}")

    asia_tech_investment_yesterday = agent.get_investment_by_region_sector('asia', 'tech', 'yesterday')
    print(f"Total investment in Asia Tech (Yesterday): ${asia_tech_investment_yesterday}")
    
    portfolio_change = agent.get_portfolio_value_change()
    print(f"Portfolio Value Change: {portfolio_change}")

    sentiments = agent.get_sentiment_trends()
    print("\nSentiment Analysis of News Headlines:")
    print(sentiments)

    aapl_price_change = agent.compare_stock_prices('AAPL')
    print(f"\nAAPL Price Change: {aapl_price_change}")

    non_existent_stock = agent.compare_stock_prices('XYZ')
    print(f"\nXYZ Price Change: {non_existent_stock}")

    nvda_asia_price_change = agent.compare_stock_prices('NVDA-AS')
    print(f"\nNVDA-AS Price Change: {nvda_asia_price_change}") 