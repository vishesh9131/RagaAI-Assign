from fastapi import FastAPI, HTTPException, Query, Path, Body
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
import os

from agents.core.scraping_agent import ScrapingAgent
from agents.core.market_agent import MarketDataAgent
from agents.core.retriever_agent import RetrieverAgent, DEFAULT_FAISS_INDEX_PATH as DEFAULT_RETRIEVER_INDEX_PATH
from agents.core.analysis_agent import AnalysisAgent
from agents.core.language_agent import LanguageAgent
from agents.core.voice_agent import VoiceAgent

# NLTK and SSL setup - run once at startup for any NLTK-dependent features
try:
    import nltk
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass 
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    required_nltk_resources = {
        "tokenizers/punkt": "punkt", 
        "taggers/averaged_perceptron_tagger": "averaged_perceptron_tagger",
        "sentiment/vader_lexicon.zip": "vader_lexicon"
    }
    for resource_path, resource_id in required_nltk_resources.items():
        try:
            nltk.data.find(resource_path)
        except nltk.downloader.DownloadError:
            print(f"NLTK resource '{resource_id}' not found. Downloading...")
            nltk.download(resource_id, quiet=False)
            print(f"NLTK resource '{resource_id}' download attempt finished.")
except ImportError:
    print("NLTK library not found. 'unstructured' features requiring NLTK may fail.")
except Exception as e:
    print(f"An error occurred during NLTK setup: {e}")

# Set Mistral API key for language agent
os.environ.setdefault("MISTRAL_API_KEY", "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

app = FastAPI(
    title="Multi-Agent Financial Data API",
    description="API endpoints for Market Data, Web Scraping, Retriever, and Analysis Agents",
    version="0.3.0"
)

# --- Initialize Agents ---
ALPHA_VANTAGE_API_KEY = None # Or "YOUR_API_KEY" or os.getenv("ALPHAVANTAGE_API_KEY")
RETRIEVER_INDEX_PATH_API = "api_faiss_store" # Separate index for API, or use a shared one

scraping_agent_instance = ScrapingAgent()
market_agent_instance = MarketDataAgent(alpha_vantage_api_key=ALPHA_VANTAGE_API_KEY)
retriever_agent_instance = RetrieverAgent(index_path=RETRIEVER_INDEX_PATH_API)
analysis_agent_instance = AnalysisAgent()
# Initialize language agent with explicit API key
language_agent_instance = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")
voice_agent_instance = VoiceAgent()

# --- Pydantic Models for Scraping Agent --- #
class ScrapeUrlRequest(BaseModel):
    url: HttpUrl

class ExtractHeadlinesRequest(BaseModel):
    url: HttpUrl
    tag: str = Query(..., description="HTML tag for headlines (e.g., h1, h2, a)")
    css_class: Optional[str] = Query(None, description="Optional CSS class of headline elements")

# --- Pydantic Models for Market Data Agent --- #
class StockSymbolPath(BaseModel):
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL, GOOGL)", min_length=1, max_length=10)

class StockPriceParams(BaseModel):
    period: str = Query("1mo", description="Period for historical data ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')")

# --- Pydantic Models for Retriever Agent --- #
class AddTextsRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, description="List of text strings to add.")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of metadata dictionaries, one per text.")

class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="The text query to search for.")
    k: int = Field(5, gt=0, le=50, description="Number of top similar documents to retrieve.")

# --- Pydantic Models for Analysis Agent --- #
class InvestmentParams(BaseModel):
    region_name: str = Field(..., example="Asia", description="The geographical region for investment analysis.")
    sector_name: str = Field(..., example="Tech", description="The market sector for investment analysis.")
    data_type: Optional[str] = Field("today", example="today", description="Data snapshot to use (today or yesterday). Must be 'today' or 'yesterday'.")

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

# --- Pydantic Models for Language Agent --- #

class SummarizeRequest(BaseModel):
    text: str = Field(..., description="Text to summarize.")
    max_words: Optional[int] = Field(150, ge=20, le=500, description="Approximate maximum word count for the summary.")

class SummarizeResponse(BaseModel):
    summary: str

class ExplainRequest(BaseModel):
    text: str = Field(..., description="Text to explain.")
    audience: Optional[str] = Field("non-expert", description="Brief description of the target audience.")

class ExplainResponse(BaseModel):
    explanation: str

# --- Pydantic Models for Voice Agent --- #

class STTResponse(BaseModel):
    text: str

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech.")
    filename: Optional[str] = Field(None, description="Optional output WAV file path")
    provider: Optional[str] = Field("pyttsx3", description="TTS provider to use")
    voice: Optional[str] = Field(None, description="Voice to use for TTS")
    api_key: Optional[str] = Field(None, description="API key for cloud providers")

class TTSResponse(BaseModel):
    wav_path: str
    provider_used: Optional[str] = None
    voice_used: Optional[str] = None

class SpeakRequest(BaseModel):
    text: str = Field(..., description="Text to speak aloud in real-time.")
    provider: Optional[str] = Field("macos_say", description="TTS provider to use")
    voice: Optional[str] = Field(None, description="Voice to use for TTS")
    api_key: Optional[str] = Field(None, description="API key for cloud providers")

class SpeakResponse(BaseModel):
    message: str
    provider_used: str
    voice_used: Optional[str] = None
    duration_seconds: Optional[float] = None

class ProvidersResponse(BaseModel):
    providers: Dict[str, Dict[str, Any]]

# --- Scraping Agent Endpoints --- #

@app.post("/scrape/html", summary="Fetch Raw HTML Content", tags=["Scraping Agent"])
async def fetch_html_endpoint(request: ScrapeUrlRequest) -> Dict[str, Any]:
    """
    Fetches the raw HTML content from the provided URL.
    """
    html_content = scraping_agent_instance.fetch_html_content(str(request.url))
    if not html_content:
        raise HTTPException(status_code=404, detail=f"Failed to fetch HTML from {request.url}. Check URL or server logs.")
    return {"url": str(request.url), "html_sample": html_content[:1000] + "... (truncated)", "length": len(html_content)}

@app.post("/scrape/headlines", summary="Extract Headlines from URL", tags=["Scraping Agent"])
async def extract_headlines_endpoint(request: ExtractHeadlinesRequest) -> Dict[str, Any]:
    """
    Extracts headlines from a URL based on HTML tag and optional CSS class.
    """
    headlines = scraping_agent_instance.extract_headlines(
        url=str(request.url), 
        headline_tag=request.tag, 
        headline_class=request.css_class
    )
    if not headlines:
        # Differentiate between no headlines found and actual error if possible
        # For now, just returning empty or raising if fetch itself failed (handled by agent)
        return {"url": str(request.url), "headlines": [], "message": "No headlines found or page could not be processed."}
    return {"url": str(request.url), "count": len(headlines), "headlines": headlines}

@app.post("/scrape/text", summary="Extract Generic Text from URL", tags=["Scraping Agent"])
async def extract_text_endpoint(request: ScrapeUrlRequest) -> Dict[str, Any]:
    """
    Extracts all paragraph text from a given URL.
    """
    text_content = scraping_agent_instance.extract_generic_text(str(request.url))
    if not text_content:
        raise HTTPException(status_code=404, detail=f"Failed to extract text from {request.url}. Check URL or server logs.")
    return {"url": str(request.url), "text_sample": text_content[:1000] + "... (truncated)", "length": len(text_content)}

@app.post("/scrape/unstructured", summary="Extract Elements with Unstructured.io", tags=["Scraping Agent"])
async def extract_unstructured_endpoint(request: ScrapeUrlRequest) -> Dict[str, Any]:
    """
    Processes a URL using Unstructured.io to extract structured elements.
    Requires 'unstructured' library to be installed with appropriate extras.
    """
    elements = scraping_agent_instance.extract_with_unstructured(url=str(request.url))
    if elements is None: # Could be due to fetch error or unstructured error
        # The agent prints specific errors to console, here we give a general one
        raise HTTPException(status_code=500, detail=f"Failed to process {str(request.url)} with Unstructured. Check server logs for details.")
    
    if isinstance(elements, dict) and "error" in elements: # Specific error from agent
        raise HTTPException(status_code=500, detail=f"Error from Unstructured agent: {elements['error']}")

    return {"url": str(request.url), "element_count": len(elements), "elements_sample": [el for el in elements[:3]]} # Sample of first 3 elements

# --- Market Data Agent Endpoints --- #

@app.get("/market/stock/{symbol}/price", summary="Get Stock Price (Yahoo Finance)", tags=["Market Data Agent"])
async def get_stock_price_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)", min_length=1, max_length=10),
    period: str = Query("1mo", description="Period for historical data ('1d', '5d', '1mo', ..., 'max')")
) -> Dict:
    data = market_agent_instance.get_stock_price(symbol.upper(), period=period)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/market/stock/{symbol}/earnings", summary="Get Earnings Data (Yahoo Finance)", tags=["Market Data Agent"])
async def get_earnings_data_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)", min_length=1, max_length=10)
) -> Dict:
    data = market_agent_instance.get_earnings_data(symbol.upper())
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/market/stock/{symbol}/info", summary="Get Company Information (Yahoo Finance)", tags=["Market Data Agent"])
async def get_company_info_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)", min_length=1, max_length=10)
) -> Dict:
    data = market_agent_instance.get_company_info(symbol.upper())
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@app.get("/market/stock/{symbol}/alphavantage", summary="Get Data from AlphaVantage", tags=["Market Data Agent"])
async def get_alpha_vantage_data_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)", min_length=1, max_length=10),
    av_function: str = Query("TIME_SERIES_DAILY", description="AlphaVantage function (e.g., 'TIME_SERIES_DAILY', 'EARNINGS')")
) -> Dict:
    if not market_agent_instance.alpha_vantage_api_key:
        raise HTTPException(status_code=501, detail="AlphaVantage API key not configured in the server.")
    data = market_agent_instance.get_alpha_vantage_data(symbol.upper(), function=av_function)
    if "error" in data:
        # AlphaVantage often returns errors within a 200 response, so check content
        if "Error Message" in data or "Information" in data: # Common AV error/info keys
            raise HTTPException(status_code=400, detail=f"AlphaVantage API error/info: {data.get('Error Message') or data.get('Information')}")
        raise HTTPException(status_code=500, detail=data["error"]) # General agent error
    if not data: # Empty response
        raise HTTPException(status_code=404, detail="No data received from AlphaVantage.")
    return data
    
@app.get("/market/search/{query}", summary="Search for Stocks (Basic)", tags=["Market Data Agent"])
async def search_stocks_endpoint(
    query: str = Path(..., description="Company name or symbol to search for")
) -> Dict:
    data = market_agent_instance.search_stocks(query)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return data

# --- Retriever Agent Endpoints --- #

@app.post("/retriever/add", summary="Add texts to the vector store", tags=["Retriever Agent"])
async def add_texts_to_retriever(request: AddTextsRequest) -> Dict[str, Any]:
    """
    Adds one or more texts to the Retriever Agent's vector store.
    Each text can optionally have associated metadata.
    """
    try:
        if request.metadatas and len(request.texts) != len(request.metadatas):
            raise HTTPException(status_code=400, 
                                detail="Number of texts and metadatas must match if metadatas are provided.")
        
        doc_ids = retriever_agent_instance.add_texts(texts=request.texts, metadatas=request.metadatas)
        return {
            "message": f"Successfully added {len(request.texts)} texts (split into chunks).", 
            "faiss_chunk_ids": doc_ids,
            "total_document_chunks": retriever_agent_instance.get_document_count()
        }
    except Exception as e:
        # Log the exception e for server-side debugging
        print(f"Error in /retriever/add: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while adding texts: {str(e)}")

@app.post("/retriever/search", summary="Search for similar texts in the vector store", tags=["Retriever Agent"])
async def search_in_retriever(request: SearchQueryRequest) -> List[Dict[str, Any]]:
    """
    Performs a similarity search for the given query in the Retriever Agent's vector store.
    """
    try:
        results = retriever_agent_instance.search(query=request.query, k=request.k)
        if results is None: # Should not happen if agent.search is robust, but as a safeguard
            raise HTTPException(status_code=500, detail="Search returned an unexpected None result.")
        return results
    except Exception as e:
        print(f"Error in /retriever/search: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during search: {str(e)}")

@app.get("/retriever/info", summary="Get information about the vector store", tags=["Retriever Agent"])
async def get_retriever_info() -> Dict[str, Any]:
    """
    Returns information about the Retriever Agent's vector store, such as document count and sources.
    """
    try:
        return {
            "index_path": retriever_agent_instance.index_path,
            "embedding_model": retriever_agent_instance.embeddings.model_name,
            "total_document_chunks": retriever_agent_instance.get_document_count(),
            "known_sources": retriever_agent_instance.list_all_chunk_sources()
        }
    except Exception as e:
        print(f"Error in /retriever/info: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching retriever info: {str(e)}")

# --- Analysis Agent Endpoints --- #

@app.post("/analysis/investment_by_region_sector", response_model=InvestmentResponse, tags=["Analysis Agent"])
async def get_investment_by_region_sector_api(params: InvestmentParams):
    """Calculates total investment in a specific region and sector."""
    if params.data_type not in ["today", "yesterday"]:
        raise HTTPException(status_code=400, detail="Invalid data_type. Choose 'today' or 'yesterday'.")
    try:
        total_investment = analysis_agent_instance.get_investment_by_region_sector(params.region_name, params.sector_name, params.data_type)
        return InvestmentResponse(
            region=params.region_name,
            sector=params.sector_name,
            data_type=params.data_type,
            total_investment=total_investment
        )
    except ValueError as e: # Catch specific error from agent
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log e for server-side debugging
        print(f"Error in /analysis/investment_by_region_sector: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/analysis/portfolio_change", response_model=PortfolioChangeResponse, tags=["Analysis Agent"])
async def get_portfolio_value_change_api():
    """Calculates the change in total portfolio value from yesterday to today."""
    try:
        change_data = analysis_agent_instance.get_portfolio_value_change()
        return PortfolioChangeResponse(**change_data)
    except Exception as e:
        print(f"Error in /analysis/portfolio_change: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/analysis/sentiment_trends", response_model=SentimentResponse, tags=["Analysis Agent"])
async def get_sentiment_trends_api(request_body: SentimentRequest):
    """Analyzes sentiment of a list of texts (e.g., news headlines)."""
    try:
        sentiments_df = analysis_agent_instance.get_sentiment_trends(texts=request_body.texts)
        sentiments_list = sentiments_df.to_dict(orient='records')
        return SentimentResponse(sentiments=[SentimentScore(**s) for s in sentiments_list])
    except Exception as e:
        print(f"Error in /analysis/sentiment_trends: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/analysis/stock_price_comparison", response_model=StockPriceCompareResponse, tags=["Analysis Agent"])
async def compare_stock_prices_api(ticker: str = Query(..., example="AAPL", description="Stock ticker symbol.")):
    """Compares yesterday's and today's price for a given stock ticker."""
    try:
        price_data = analysis_agent_instance.compare_stock_prices(ticker)
        # Ensure ticker is included in the response even if there's an error and it's not in price_data
        if "error" in price_data and "ticker" not in price_data:
             price_data["ticker"] = ticker
        return StockPriceCompareResponse(**price_data)
    except Exception as e:
        print(f"Error in /analysis/stock_price_comparison: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Language Agent Endpoints --- #

@app.post("/language/summarize", response_model=SummarizeResponse, summary="Summarize text", tags=["Language Agent"])
async def summarize_text_api(request_body: SummarizeRequest):
    summary = language_agent_instance.summarize(request_body.text, max_words=request_body.max_words)
    if not summary:
        raise HTTPException(status_code=400, detail="Could not generate summary. Ensure text is non-empty.")
    return SummarizeResponse(summary=summary)

@app.post("/language/explain", response_model=ExplainResponse, summary="Explain text", tags=["Language Agent"])
async def explain_text_api(request_body: ExplainRequest):
    explanation = language_agent_instance.explain(request_body.text, target_audience=request_body.audience)
    if not explanation:
        raise HTTPException(status_code=400, detail="Could not generate explanation. Ensure text is non-empty.")
    return ExplainResponse(explanation=explanation)

# --- Voice Agent Endpoints --- #

@app.post("/voice/stt", response_model=STTResponse, summary="Speech ➜ Text (Whisper)", tags=["Voice Agent"])
async def speech_to_text_api(audio_bytes: bytes = Body(..., media_type="audio/wav")):
    """Transcribe uploaded WAV audio (raw bytes) to text using Whisper."""
    import tempfile, pathlib
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = pathlib.Path(tmp.name)
    try:
        text = voice_agent_instance.speech_to_text(tmp_path)
        return STTResponse(text=text)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

@app.post("/voice/tts", response_model=TTSResponse, summary="Text ➜ Speech (pyttsx3)", tags=["Voice Agent"])
async def text_to_speech_api(request: TTSRequest):
    """Convert text to speech and save to file."""
    try:
        # Create temporary agent with specified parameters if provided
        if request.provider != "pyttsx3" or request.voice or request.api_key:
            temp_agent = VoiceAgent(
                tts_provider=request.provider or "pyttsx3",
                tts_voice=request.voice,
                api_key=request.api_key
            )
            wav_path = temp_agent.text_to_speech(request.text, output_path=request.filename)
            return TTSResponse(
                wav_path=wav_path,
                provider_used=temp_agent.tts_provider,
                voice_used=temp_agent.tts_voice
            )
        else:
            # Use existing instance for backward compatibility
            wav_path = voice_agent_instance.text_to_speech(request.text, output_path=request.filename)
            return TTSResponse(
                        wav_path=wav_path,
                        provider_used=voice_agent_instance.tts_provider,
                        voice_used=voice_agent_instance.tts_voice
                    )
    except Exception as e:
            print(f"Error in /voice/tts: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/voice/speak", response_model=SpeakResponse, summary="Text ➜ Speech (real-time)", tags=["Voice Agent"])
async def speak_text_api(request: SpeakRequest):
    """Convert text to speech in real-time using a specified TTS provider and voice."""
    try:
        message, provider_used, voice_used, duration_seconds = voice_agent_instance.speak(request.text, request.provider, request.voice, request.api_key)
        return SpeakResponse(
            message=message,
            provider_used=provider_used,
            voice_used=voice_used,
            duration_seconds=duration_seconds
        )
    except Exception as e:
        print(f"Error in /voice/speak: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/voice/providers", response_model=ProvidersResponse, summary="Get available TTS providers and voices", tags=["Voice Agent"])
async def get_providers_api():
    """Get a list of available TTS providers and voices."""
    try:
        providers = voice_agent_instance.get_providers()
        return ProvidersResponse(providers=providers)
    except Exception as e:
        print(f"Error in /voice/providers: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # It's recommended to run Uvicorn from the command line for more options:
    # uvicorn main:app --reload
    # Ensure RETRIEVER_INDEX_PATH_API directory exists or can be created by the agent
    if not os.path.exists(RETRIEVER_INDEX_PATH_API):
        os.makedirs(RETRIEVER_INDEX_PATH_API)
        print(f"Created directory for FAISS index: {RETRIEVER_INDEX_PATH_API}")

    uvicorn.run(app, host="0.0.0.0", port=8000) 