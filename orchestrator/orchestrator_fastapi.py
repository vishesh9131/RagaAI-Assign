from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64, tempfile, pathlib, re, json
import os
import numpy as np
import uuid
import time
from datetime import datetime

from agents.core.voice_agent import VoiceAgent
from agents.core.retriever_agent import RetrieverAgent
from agents.core.analysis_agent import AnalysisAgent
from agents.core.language_agent import LanguageAgent
from agents.core.market_agent import MarketDataAgent
from agents.core.scraping_agent import ScrapingAgent

app = FastAPI(
    title="Intelligent Financial Assistant Orchestrator",
    description="AI-powered orchestrator that routes queries to appropriate agents and provides natural language responses.",
    version="2.0.0"
)

# Add environment variable for Mistral API key at the top
os.environ.setdefault("MISTRAL_API_KEY", "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

# Global status tracking for real-time updates
execution_status_store = {}

# Initialize all agents
voice_agent = VoiceAgent()
retriever_agent = RetrieverAgent(index_path="orchestrator_faiss")
analysis_agent = AnalysisAgent()
language_agent = LanguageAgent(model_name="open-mistral-nemo", api_key="NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")
market_agent = MarketDataAgent()
scraping_agent = ScrapingAgent()

# -------------------------------  MODELS  -------------------------------
class IntelligentQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query about financial data, market analysis, or general information")
    voice_mode: bool = Field(False, description="Return TTS audio in addition to text")
    include_debug_info: bool = Field(False, description="Include debug information about agent routing")

class AgentExecutionStatus(BaseModel):
    agent_name: str
    status: str  # "waiting", "executing", "completed", "failed"
    description: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ExecutionProgress(BaseModel):
    session_id: str
    query: str
    current_step: str
    agents_status: List[AgentExecutionStatus]
    overall_status: str  # "initializing", "routing", "executing", "completed", "failed"
    progress_percentage: float

class IntelligentResponse(BaseModel):
    response_text: str
    agents_used: List[AgentExecutionStatus]
    query_interpretation: str
    wav_audio_base64: Optional[str] = None
    confidence: float = Field(description="Confidence in query understanding (0-1)")
    session_id: str

# -------------------------------  QUERY ROUTER  -------------------------------
class QueryRouter:
    def __init__(self):
        self.patterns = {
            "market_data": [
                r"stock", r"price", r"share", r"ticker", r"market", r"trading", r"volume", r"quote",
                r"AAPL", r"GOOGL", r"MSFT", r"TSLA", r"AMZN", r"META", r"NVDA", r"NFLX", r"SPY", r"QQQ",
                r"earnings", r"revenue", r"profit", r"financial", r"company", r"corporation", r"business",
                r"dividend", r"yield", r"market cap", r"P/E", r"ratio", r"valuation", r"fundamentals",
                r"NYSE", r"NASDAQ", r"exchange", r"IPO", r"listing", r"symbol"
            ],
            "analysis": [
                r"analyz", r"compar", r"performance", r"trend", r"pattern", r"forecast", r"predict",
                r"investment", r"portfolio", r"diversif", r"risk", r"return", r"yield", r"growth",
                r"sector", r"industry", r"region", r"market", r"economy", r"economic", r"financial",
                r"sentiment", r"bullish", r"bearish", r"volatile", r"stability", r"correlation",
                r"recommend", r"advise", r"strategy", r"allocation", r"hedge", r"balance",
                r"tech", r"technology", r"auto", r"automotive", r"healthcare", r"energy", r"finance",
                r"Asia", r"Europe", r"US", r"America", r"emerging", r"developed", r"international"
            ],
            "scraping": [
                r"news", r"headlines", r"article", r"report", r"announcement", r"press release",
                r"latest", r"recent", r"current", r"today", r"update", r"breaking", r"development",
                r"website", r"url", r"scrape", r"extract", r"content", r"information",
                r"reuters", r"bloomberg", r"wsj", r"financial times", r"cnbc", r"marketwatch",
                r"SEC filing", r"10-K", r"10-Q", r"8-K", r"regulatory", r"filing"
            ],
            "retrieval": [
                r"search", r"find", r"look", r"retrieve", r"get", r"show", r"display",
                r"database", r"stored", r"saved", r"historical", r"past", r"previous",
                r"document", r"record", r"data", r"information", r"details", r"facts",
                r"research", r"study", r"analysis", r"insight", r"knowledge", r"learn"
            ],
            "explanation": [
                r"explain", r"what", r"how", r"why", r"define", r"definition", r"meaning",
                r"tell", r"describe", r"detail", r"elaborate", r"clarify", r"understand",
                r"concept", r"term", r"process", r"method", r"principle", r"theory",
                r"help", r"guide", r"tutorial", r"example", r"overview", r"summary"
            ]
        }
    
    def classify_query(self, query: str) -> List[str]:
        """Classify query into agent categories with intelligent multi-agent routing."""
        query_lower = query.lower()
        matched_agents = []
        agent_scores = {}
        
        # Score each agent based on pattern matches
        for agent_type, patterns in self.patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            
            if score > 0:
                agent_scores[agent_type] = score
        
        # Enhanced routing logic for comprehensive analysis
        financial_terms = ["stock", "price", "market", "financial", "company", "investment", "portfolio"]
        has_financial_terms = any(term in query_lower for term in financial_terms)
        
        # Always include market_data for financial queries
        if has_financial_terms and "market_data" not in agent_scores:
            agent_scores["market_data"] = 1
        
        # Always include analysis for complex queries
        complex_indicators = ["analyze", "compare", "performance", "trend", "recommend", "vs", "versus", "better", "best"]
        if any(indicator in query_lower for indicator in complex_indicators):
            agent_scores["analysis"] = agent_scores.get("analysis", 0) + 2
        
        # Include retrieval for information seeking queries
        info_seeking = ["what", "how", "why", "tell", "explain", "show", "find", "search"]
        if any(word in query_lower for word in info_seeking):
            agent_scores["retrieval"] = agent_scores.get("retrieval", 0) + 1
        
        # Include scraping for current/latest information
        current_info = ["latest", "current", "today", "recent", "news", "update"]
        if any(word in query_lower for word in current_info):
            agent_scores["scraping"] = agent_scores.get("scraping", 0) + 1
        
        # Always include explanation for educational queries
        educational = ["explain", "what is", "how does", "definition", "meaning"]
        if any(phrase in query_lower for phrase in educational):
            agent_scores["explanation"] = agent_scores.get("explanation", 0) + 1
        
        # Sort agents by score and select top agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Select agents with meaningful scores, but ensure at least 2 agents for comprehensive analysis
        threshold = max(1, max(agent_scores.values()) * 0.3) if agent_scores else 1
        selected_agents = [agent for agent, score in sorted_agents if score >= threshold]
        
        # Ensure minimum agent diversity for comprehensive analysis
        if len(selected_agents) < 2 and agent_scores:
            # Add the next best agents
            remaining_agents = [agent for agent, score in sorted_agents if agent not in selected_agents]
            selected_agents.extend(remaining_agents[:2-len(selected_agents)])
        
        # If still no agents, default to explanation + market_data for financial queries
        if not selected_agents:
            if has_financial_terms:
                selected_agents = ["market_data", "explanation"]
            else:
                selected_agents = ["explanation", "retrieval"]
        
        # Limit to maximum 4 agents for performance
        selected_agents = selected_agents[:4]
        
        print(f"DEBUG: Query '{query}' scored agents: {agent_scores}")
        print(f"DEBUG: Selected agents: {selected_agents}")
        
        return selected_agents

# Initialize router
query_router = QueryRouter()

# -------------------------------  AGENT EXECUTORS  -------------------------------
async def execute_market_agent(query: str, interpretation: str, session_id: str) -> AgentExecutionStatus:
    """Execute market data queries."""
    status = AgentExecutionStatus(
        agent_name="Market Agent",
        status="executing",
        description="Fetching stock market data and financial information",
        start_time=datetime.now()
    )
    
    # Update status to executing
    update_agent_status(session_id, status)
    
    try:
        # Extract ticker symbol if present - improved regex
        ticker_mapping = {
            "apple": "AAPL", "aapl": "AAPL",
            "tesla": "TSLA", "tsla": "TSLA", 
            "microsoft": "MSFT", "msft": "MSFT",
            "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
            "amazon": "AMZN", "amzn": "AMZN",
            "meta": "META", "facebook": "META",
            "nvidia": "NVDA", "nvda": "NVDA"
        }
        
        # Extract all potential tickers
        found_tickers = []
        query_lower = query.lower()
        
        # Check for company names and common tickers
        for name, ticker_symbol in ticker_mapping.items():
            if name in query_lower:
                found_tickers.append(ticker_symbol)
        
        # Also look for uppercase ticker patterns, excluding common words
        ticker_patterns = re.findall(r'\b([A-Z]{2,5})\b', query.upper())
        excluded_words = {"WHAT", "THE", "AND", "FOR", "WITH", "FROM", "THAT", "THIS", "HOW", "ARE", "CAN", "WILL"}
        for pattern in ticker_patterns:
            if pattern not in excluded_words and pattern not in found_tickers:
                found_tickers.append(pattern)
        
        # Use first valid ticker or default to AAPL
        ticker = found_tickers[0] if found_tickers else "AAPL"
        
        # Update status with specific action
        status.description = f"Analyzing query for {ticker}..."
        update_agent_status(session_id, status)
        
        # Determine the type of market data request
        if any(word in query.lower() for word in ["price", "stock", "share"]):
            status.description = f"Fetching stock price for {ticker}..."
            update_agent_status(session_id, status)
            result = market_agent.get_stock_price(ticker)
            status.description = f"Retrieved stock price data for {ticker}"
        elif any(word in query.lower() for word in ["earnings", "financial"]):
            status.description = f"Fetching earnings data for {ticker}..."
            update_agent_status(session_id, status)
            result = market_agent.get_earnings_data(ticker)
            status.description = f"Retrieved earnings data for {ticker}"
        elif any(word in query.lower() for word in ["company", "info", "information"]):
            status.description = f"Fetching company information for {ticker}..."
            update_agent_status(session_id, status)
            result = market_agent.get_company_info(ticker)
            status.description = f"Retrieved company information for {ticker}"
        else:
            status.description = f"Fetching default stock data for {ticker}..."
            update_agent_status(session_id, status)
            result = market_agent.get_stock_price(ticker)
            status.description = f"Retrieved default stock data for {ticker}"
        
        status.status = "completed"
        status.result = result
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status
        
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status

async def execute_analysis_agent(query: str, interpretation: str, session_id: str) -> AgentExecutionStatus:
    """Execute financial analysis queries."""
    status = AgentExecutionStatus(
        agent_name="Analysis Agent",
        status="executing",
        description="Performing financial analysis and calculations",
        start_time=datetime.now()
    )
    
    # Update status to executing
    update_agent_status(session_id, status)
    
    try:
        # Determine analysis type
        if any(word in query.lower() for word in ["investment", "region", "sector"]):
            status.description = "Analyzing investment by region and sector..."
            update_agent_status(session_id, status)
            # Extract region and sector
            region = "Asia" if "asia" in query.lower() else "US"
            sector = "Tech" if "tech" in query.lower() else "Tech"
            result = {"investment": analysis_agent.get_investment_by_region_sector(region, sector)}
            result = convert_numpy_types(result)
            status.description = f"Calculated investment for {region} {sector} sector"
        
        elif any(word in query.lower() for word in ["portfolio", "change", "performance"]):
            status.description = "Calculating portfolio performance..."
            update_agent_status(session_id, status)
            result = analysis_agent.get_portfolio_value_change()
            result = convert_numpy_types(result)
            status.description = "Calculated portfolio value changes"
        
        elif any(word in query.lower() for word in ["sentiment", "news", "headlines"]):
            status.description = "Analyzing sentiment of news headlines..."
            update_agent_status(session_id, status)
            result = {"sentiments": analysis_agent.get_sentiment_trends().to_dict('records')}
            result = convert_numpy_types(result)
            status.description = "Analyzed sentiment of news headlines"
        
        elif any(word in query.lower() for word in ["compare", "price"]):
            status.description = "Comparing stock prices..."
            update_agent_status(session_id, status)
            
            # Enhanced ticker extraction - look for common ticker symbols and company names
            ticker_mapping = {
                "apple": "AAPL", "aapl": "AAPL",
                "tesla": "TSLA", "tsla": "TSLA", 
                "microsoft": "MSFT", "msft": "MSFT",
                "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
                "amazon": "AMZN", "amzn": "AMZN",
                "meta": "META", "facebook": "META",
                "nvidia": "NVDA", "nvda": "NVDA"
            }
            
            # Extract all potential tickers
            found_tickers = []
            query_lower = query.lower()
            
            # Check for company names and common tickers
            for name, ticker in ticker_mapping.items():
                if name in query_lower:
                    found_tickers.append(ticker)
            
            # Also look for uppercase ticker patterns, excluding common words
            ticker_patterns = re.findall(r'\b([A-Z]{2,5})\b', query.upper())
            excluded_words = {"WHAT", "THE", "AND", "FOR", "WITH", "FROM", "THAT", "THIS", "HOW", "ARE", "CAN", "WILL"}
            for pattern in ticker_patterns:
                if pattern not in excluded_words and pattern not in found_tickers:
                    found_tickers.append(pattern)
            
            # Use first valid ticker or default to AAPL
            ticker = found_tickers[0] if found_tickers else "AAPL"
            
            result = analysis_agent.compare_stock_prices(ticker)
            result = convert_numpy_types(result)
            status.description = f"Compared stock prices for {ticker}"
        
        elif any(word in query.lower() for word in ["trends", "market"]):
            status.description = "Identifying market trends..."
            update_agent_status(session_id, status)
            region = "Asia" if "asia" in query.lower() else "US"
            sector = "Tech" if "tech" in query.lower() else "Tech"
            result = {"trends": analysis_agent.identify_market_trends(sector, region)}
            result = convert_numpy_types(result)
            status.description = f"Analyzed market trends for {region} {sector}"
        
        else:
            status.description = "Performing general portfolio analysis..."
            update_agent_status(session_id, status)
            result = analysis_agent.get_portfolio_value_change()
            result = convert_numpy_types(result)
            status.description = "Performed general portfolio analysis"
        
        status.status = "completed"
        status.result = result
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status
        
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status

async def execute_scraping_agent(query: str, interpretation: str, session_id: str) -> AgentExecutionStatus:
    """Execute web scraping queries."""
    status = AgentExecutionStatus(
        agent_name="Scraping Agent",
        status="executing",
        description="Scraping web content and extracting information",
        start_time=datetime.now()
    )
    
    # Update status to executing
    update_agent_status(session_id, status)
    
    try:
        # Extract URL if present
        url_match = re.search(r'https?://[^\s]+', query)
        if url_match:
            url = url_match.group(0)
        else:
            # Default to a financial news site
            url = "https://finance.yahoo.com"
        
        status.description = f"Connecting to {url}..."
        update_agent_status(session_id, status)
        
        # Determine scraping type
        if any(word in query.lower() for word in ["headlines", "news"]):
            status.description = f"Extracting headlines from {url}..."
            update_agent_status(session_id, status)
            result = {"headlines": scraping_agent.extract_headlines(url, "h3")}
            status.description = f"Extracted headlines from {url}"
        else:
            status.description = f"Extracting content from {url}..."
            update_agent_status(session_id, status)
            result = {"text": scraping_agent.extract_generic_text(url)}
            status.description = f"Extracted text content from {url}"
        
        status.status = "completed"
        status.result = result
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status
        
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status

async def execute_retrieval_agent(query: str, interpretation: str, session_id: str) -> AgentExecutionStatus:
    """Execute document retrieval queries."""
    status = AgentExecutionStatus(
        agent_name="Retriever Agent",
        status="executing",
        description="Searching stored documents and information",
        start_time=datetime.now()
    )
    
    # Update status to executing
    update_agent_status(session_id, status)
    
    try:
        status.description = "Searching document database..."
        update_agent_status(session_id, status)
        
        # Search for relevant documents
        results = retriever_agent.search(query, k=3)
        
        status.status = "completed"
        status.result = {"search_results": results}
        status.description = f"Found {len(results)} relevant documents"
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status
        
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status

async def execute_explanation_agent(query: str, interpretation: str, session_id: str) -> AgentExecutionStatus:
    """Execute explanation queries."""
    status = AgentExecutionStatus(
        agent_name="Language Agent",
        status="executing",
        description="Explaining the query interpretation",
        start_time=datetime.now()
    )
    
    # Update status to executing
    update_agent_status(session_id, status)
    
    try:
        status.description = "Explaining the query interpretation..."
        update_agent_status(session_id, status)
        
        interpretation_prompt = f"""
        Analyze this financial/business query and provide a brief interpretation of what the user is asking for:
        Query: "{query}"
        
        Interpretation:"""
        
        try:
            query_interpretation = language_agent.explain(interpretation_prompt, target_audience="system")
        except Exception as e:
            print(f"DEBUG: Language agent failed: {e}")
            query_interpretation = f"Query interpretation failed: {e}"
        
        status.status = "completed"
        status.result = query_interpretation
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status
        
    except Exception as e:
        status.status = "failed"
        status.error = str(e)
        status.end_time = datetime.now()
        update_agent_status(session_id, status)
        return status

# -------------------------------  MAIN ORCHESTRATOR  -------------------------------
async def process_intelligent_query(query: str, voice_mode: bool = False, include_debug: bool = False) -> IntelligentResponse:
    """Process an intelligent query using multiple agents and natural language understanding."""
    
    # Create execution session
    session_id = create_execution_session(query)
    
    try:
        # Step 1: Interpret the query using language agent
        update_execution_status(session_id, "Interpreting query", "routing", 10.0)
        
        interpretation_prompt = f"""
        Analyze this financial/business query and provide a brief interpretation of what the user is asking for:
        Query: "{query}"
        
        Interpretation:"""
        
        try:
            query_interpretation = language_agent.explain(interpretation_prompt, target_audience="system")
        except Exception as e:
            print(f"DEBUG: Language agent failed: {e}")
            query_interpretation = f"Query interpretation failed: {e}"
        
        # Step 2: Route to appropriate agents
        update_execution_status(session_id, "Routing to agents", "routing", 20.0)
        agent_types = query_router.classify_query(query)
        
        # Initialize agent statuses as "waiting"
        for agent_type in agent_types:
            agent_name_map = {
                "market_data": "Market Agent",
                "analysis": "Analysis Agent", 
                "scraping": "Scraping Agent",
                "retrieval": "Retriever Agent",
                "explanation": "Language Agent"
            }
            waiting_status = AgentExecutionStatus(
                agent_name=agent_name_map.get(agent_type, f"{agent_type.title()} Agent"),
                status="waiting",
                description="Waiting for execution"
            )
            update_agent_status(session_id, waiting_status)
        
        agents_used = []
        all_results = {}
        total_agents = len(agent_types)
        
        # Step 3: Execute agents sequentially with progress updates
        update_execution_status(session_id, "Executing agents", "executing", 30.0)
        
        print(f"DEBUG: About to execute {len(agent_types)} agents: {agent_types}")  # Debug print
        
        for i, agent_type in enumerate(agent_types):
            progress = 30.0 + ((i + 1) / total_agents) * 50.0  # 30-80% for agent execution
            
            print(f"DEBUG: Executing agent {i+1}/{total_agents}: {agent_type}")  # Debug print
            
            if agent_type == "market_data":
                update_execution_status(session_id, "Executing Market Agent", "executing", progress)
                result = await execute_market_agent(query, query_interpretation, session_id)
                agents_used.append(result)
                print(f"DEBUG: Market agent result: {result.status}")  # Debug print
                if result.result:
                    all_results["market_data"] = result.result
                    
            elif agent_type == "analysis":
                update_execution_status(session_id, "Executing Analysis Agent", "executing", progress)
                result = await execute_analysis_agent(query, query_interpretation, session_id)
                agents_used.append(result)
                print(f"DEBUG: Analysis agent result: {result.status}")  # Debug print
                if result.result:
                    all_results["analysis"] = result.result
                    
            elif agent_type == "scraping":
                update_execution_status(session_id, "Executing Scraping Agent", "executing", progress)
                result = await execute_scraping_agent(query, query_interpretation, session_id)
                agents_used.append(result)
                print(f"DEBUG: Scraping agent result: {result.status}")  # Debug print
                if result.result:
                    all_results["scraping"] = result.result
                    
            elif agent_type == "retrieval":
                update_execution_status(session_id, "Executing Retriever Agent", "executing", progress)
                result = await execute_retrieval_agent(query, query_interpretation, session_id)
                agents_used.append(result)
                print(f"DEBUG: Retrieval agent result: {result.status}")  # Debug print
                if result.result:
                    all_results["retrieval"] = result.result
                    
            elif agent_type == "explanation":
                update_execution_status(session_id, "Executing Language Agent", "executing", progress)
                result = await execute_explanation_agent(query, query_interpretation, session_id)
                agents_used.append(result)
                print(f"DEBUG: Explanation agent result: {result.status}")  # Debug print
                if result.result:
                    all_results["explanation"] = result.result
        
        print(f"DEBUG: Final agents_used length: {len(agents_used)}")  # Debug print
        
        # Step 4: Generate natural language response
        update_execution_status(session_id, "Generating response", "executing", 85.0)
        
        response_prompt = f"""
        User Query: "{query}"
        
        Available Data:
        {json.dumps(all_results, indent=2, default=str)[:2000]}...
        
        Create a clear, helpful response that answers the user's question using the available data. 
        Be conversational and explain the findings in simple terms.
        
        Response:"""
        
        try:
            if all_results:
                natural_response = language_agent.summarize(response_prompt, max_words=200)
            else:
                natural_response = language_agent.explain(query, target_audience="general")
        except Exception as e:
            print(f"DEBUG: Response generation failed: {e}")
            if all_results:
                natural_response = f"I found some data but couldn't generate a proper response: {str(all_results)[:200]}..."
            else:
                natural_response = f"I couldn't process your query properly. Error: {e}"
        
        # Step 5: Calculate confidence
        confidence = 0.9 if len([a for a in agents_used if a.status == "completed"]) > 0 else 0.3
        
        # Step 6: Generate audio if requested
        update_execution_status(session_id, "Finalizing response", "executing", 95.0)
        wav_b64 = None
        if voice_mode:
            print(f"DEBUG: Voice mode enabled, attempting TTS for text: '{natural_response[:50]}...'")
            try:
                wav_path = voice_agent.text_to_speech(natural_response)
                print(f"DEBUG: TTS created file at: {wav_path}")
                with open(wav_path, "rb") as f:
                    wav_b64 = base64.b64encode(f.read()).decode()
                print(f"DEBUG: Successfully encoded audio to base64, length: {len(wav_b64) if wav_b64 else 0}")
            except Exception as e:
                print(f"DEBUG: TTS failed with error: {e}")
                import traceback
                traceback.print_exc()
        
        # Mark as completed
        update_execution_status(session_id, "Completed", "completed", 100.0)
        
        return IntelligentResponse(
            response_text=natural_response,
            agents_used=agents_used,
            query_interpretation=query_interpretation,
            wav_audio_base64=wav_b64,
            confidence=confidence,
            session_id=session_id
        )
    
    except Exception as e:
        update_execution_status(session_id, f"Failed: {str(e)}", "failed", 0.0)
        raise e

# -------------------------------  ROUTES  -------------------------------
@app.post("/intelligent/query", response_model=IntelligentResponse, summary="Intelligent Query Processing")
async def intelligent_query_endpoint(request: IntelligentQueryRequest):
    """
    Process natural language queries intelligently by routing to appropriate agents
    and providing natural language responses.
    """
    return await process_intelligent_query(
        request.query, 
        request.voice_mode, 
        request.include_debug_info
    )

@app.post("/intelligent/voice", response_model=IntelligentResponse, summary="Voice Query Processing")
async def intelligent_voice_endpoint(
    audio: UploadFile = File(...), 
    voice_mode: bool = Form(True),
    include_debug: bool = Form(False)
):
    """
    Process voice queries intelligently by converting speech to text,
    routing to appropriate agents, and providing natural language responses.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await audio.read())
        tmp_path = pathlib.Path(tmp.name)
    
    try:
        user_text = voice_agent.speech_to_text(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    
    return await process_intelligent_query(user_text.strip(), voice_mode, include_debug)

@app.get("/execution/status/{session_id}", response_model=ExecutionProgress, summary="Get Real-time Execution Status")
async def get_execution_status(session_id: str):
    """Get the real-time execution status for a specific session."""
    if session_id not in execution_status_store:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return execution_status_store[session_id]

@app.delete("/execution/status/{session_id}", summary="Clean up Execution Session")
async def cleanup_execution_status(session_id: str):
    """Clean up execution session data."""
    if session_id in execution_status_store:
        del execution_status_store[session_id]
        return {"message": "Session cleaned up successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/agents/status", summary="Get Agent Status")
async def get_agent_status():
    """Get the current status of all available agents."""
    return {
        "available_agents": [
            {"name": "Market Agent", "description": "Stock prices, company info, earnings data", "status": "active"},
            {"name": "Analysis Agent", "description": "Portfolio analysis, sentiment analysis, market trends", "status": "active"},
            {"name": "Language Agent", "description": "Text summarization and explanation powered by Mistral AI", "status": "active"},
            {"name": "Retriever Agent", "description": "Document search and retrieval", "status": "active"},
            {"name": "Scraping Agent", "description": "Web content extraction", "status": "active"},
            {"name": "Voice Agent", "description": "Speech-to-text and text-to-speech", "status": "active"}
        ],
        "orchestrator_version": "2.0.0",
        "language_model": "Mistral AI open-mistral-nemo",
        "active_sessions": len(execution_status_store)
    }

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

# -------------------------------  STATUS TRACKING  -------------------------------
def create_execution_session(query: str) -> str:
    """Create a new execution session and return session ID."""
    session_id = str(uuid.uuid4())
    execution_status_store[session_id] = ExecutionProgress(
        session_id=session_id,
        query=query,
        current_step="Initializing",
        agents_status=[],
        overall_status="initializing",
        progress_percentage=0.0
    )
    return session_id

def update_execution_status(session_id: str, step: str, overall_status: str, progress: float):
    """Update the overall execution status."""
    if session_id in execution_status_store:
        execution_status_store[session_id].current_step = step
        execution_status_store[session_id].overall_status = overall_status
        execution_status_store[session_id].progress_percentage = progress

def update_agent_status(session_id: str, agent_status: AgentExecutionStatus):
    """Update or add agent status."""
    if session_id in execution_status_store:
        # Find and update existing agent status or add new one
        agents = execution_status_store[session_id].agents_status
        for i, existing_agent in enumerate(agents):
            if existing_agent.agent_name == agent_status.agent_name:
                agents[i] = agent_status
                return
        # If not found, add new agent status
        agents.append(agent_status)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011) 