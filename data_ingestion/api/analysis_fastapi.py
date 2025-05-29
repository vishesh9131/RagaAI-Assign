from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd

from analysis_agent import AnalysisAgent

app = FastAPI(
    title="Analysis Agent API",
    description="API for financial analysis tasks like investment calculation, portfolio changes, and sentiment analysis.",
    version="1.0.0"
)

agent = AnalysisAgent()

class InvestmentParams(BaseModel):
    region_name: str = Field(..., example="Asia", description="The geographical region for investment analysis.")
    sector_name: str = Field(..., example="Tech", description="The market sector for investment analysis.")
    data_type: Optional[str] = Field("today", example="today", choices=['today', 'yesterday'], description="Data snapshot to use (today or yesterday).")

class InvestmentResponse(BaseModel):
    region: str
    sector: str
    data_type: str
    total_investment: float

class PortfolioChangeResponse(BaseModel):
    yesterday_value: float
    today_value: float
    change: float
    percentage_change: float

class SentimentRequest(BaseModel):
    texts: Optional[List[str]] = Field(None, example=["Stock market is booming!", "Economic downturn expected."], description="List of texts to analyze. Uses default headlines if not provided.")

class SentimentScore(BaseModel):
    text: str
    positive: float
    negative: float
    neutral: float
    compound: float

class SentimentResponse(BaseModel):
    sentiments: List[SentimentScore]

class StockPriceCompareResponse(BaseModel):
    ticker: str
    yesterday_price: float
    today_price: float
    price_change: float
    percentage_price_change: float
    error: Optional[str] = None

@app.post("/analysis/investment_by_region_sector", response_model=InvestmentResponse, tags=["Analysis"])
async def get_investment_by_region_sector_api(params: InvestmentParams):
    """Calculates total investment in a specific region and sector."""
    try:
        total_investment = agent.get_investment_by_region_sector(params.region_name, params.sector_name, params.data_type)
        return InvestmentResponse(
            region=params.region_name,
            sector=params.sector_name,
            data_type=params.data_type,
            total_investment=total_investment
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/analysis/portfolio_change", response_model=PortfolioChangeResponse, tags=["Analysis"])
async def get_portfolio_value_change_api():
    """Calculates the change in total portfolio value from yesterday to today."""
    try:
        change_data = agent.get_portfolio_value_change()
        return PortfolioChangeResponse(**change_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/analysis/sentiment_trends", response_model=SentimentResponse, tags=["Analysis"])
async def get_sentiment_trends_api(request_body: SentimentRequest):
    """Analyzes sentiment of a list of texts (e.g., news headlines)."""
    try:
        sentiments_df = agent.get_sentiment_trends(texts=request_body.texts)
        # Convert DataFrame to list of dicts for Pydantic model
        sentiments_list = sentiments_df.to_dict(orient='records')
        return SentimentResponse(sentiments=[SentimentScore(**s) for s in sentiments_list])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/analysis/stock_price_comparison", response_model=StockPriceCompareResponse, tags=["Analysis"])
async def compare_stock_prices_api(ticker: str = Query(..., example="AAPL", description="Stock ticker symbol.")):
    """Compares yesterday's and today's price for a given stock ticker."""
    try:
        price_data = agent.compare_stock_prices(ticker)
        if "error" in price_data:
            return StockPriceCompareResponse(**price_data, ticker=ticker) # ticker might not be in price_data if error
        return StockPriceCompareResponse(**price_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Note: This is for development. For production, use a Gunicorn or similar.
    # The agent.portfolio_data and agent.news_headlines are placeholders.
    # In a real system, this data would be managed and updated dynamically.
    uvicorn.run(app, host="0.0.0.0", port=8002) 