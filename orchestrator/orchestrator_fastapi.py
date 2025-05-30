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

# Store initialized agents globally to be accessed by Streamlit after initialization
_initialized_agents = {}

def initialize_agents():
    """Initializes all agents and stores them in a global dictionary."""
    global _initialized_agents
    if not _initialized_agents: # Initialize only once
        _initialized_agents = {
            "voice_agent": VoiceAgent(),
            "retriever_agent": RetrieverAgent(index_path="orchestrator_faiss"),
            "analysis_agent": AnalysisAgent(),
            "language_agent": LanguageAgent(model_name="open-mistral-nemo", api_key=os.environ.get("MISTRAL_API_KEY")),
            "market_agent": MarketDataAgent(),
            "scraping_agent": ScrapingAgent()
        }
    return _initialized_agents

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
    """Process intelligent query by routing to appropriate agents."""
    session_id = create_execution_session(query)
    
    # Ensure agents are initialized
    agents = _initialized_agents if _initialized_agents else initialize_agents()
    language_agent_instance = agents["language_agent"]
    voice_agent_instance = agents["voice_agent"]
    retriever_agent_instance = agents["retriever_agent"]
    analysis_agent_instance = agents["analysis_agent"]
    market_agent_instance = agents["market_agent"]
    scraping_agent_instance = agents["scraping_agent"]

    update_execution_status(session_id, "Initializing", "initializing", 5.0)
    
    # Generate a more human-readable query interpretation
    try:
        interpretation_prompt = (
            f"Analyze the following user query: '{query}'. "
            "Provide a concise, one-sentence interpretation of what the user is asking. "
            "Focus on the core intent and key entities. For example, if the query is "
            "'What's the current stock price of Apple and tell me news about Tesla?', "
            "the interpretation could be 'The user wants the current stock price for AAPL and recent news about TSLA.' "
            "If the query is complex, break it down slightly, like 'User wants to compare financial performance of MSFT and GOOGL, and retrieve recent news about NVDA.'"
        )
        interpretation_response = await language_agent_instance.generate_response_async(interpretation_prompt, max_tokens=100)
        query_interpretation = interpretation_response.strip()
        confidence = 0.9 # Default confidence, can be refined
    except Exception as e:
        print(f"Error generating query interpretation: {e}")
        query_interpretation = f"Interpreted query: {query}" # Fallback
        confidence = 0.6
    
    update_execution_status(session_id, "Query Interpretation", "routing", 10.0)
    
    # Use QueryRouter to determine agents
    # Ensure the query_router is initialized if it's not part of the class structure that's auto-initialized
    # For now, assuming query_router is available globally as initialized in the original file
    selected_agent_types = query_router.classify_query(query_interpretation) 
    
    update_execution_status(session_id, f"Identified Agents: {', '.join(selected_agent_types)}", "routing", 20.0)

    all_agent_results = []
    final_response_parts = []
    
    agent_execution_map = {
        "market_data": (execute_market_agent, market_agent_instance),
        "analysis": (execute_analysis_agent, analysis_agent_instance),
        "scraping": (execute_scraping_agent, scraping_agent_instance),
        "retrieval": (execute_retrieval_agent, retriever_agent_instance),
        "explanation": (execute_explanation_agent, language_agent_instance) # Explanation uses language agent
    }
    
    for agent_type in selected_agent_types:
        try:
            execute_func, agent_instance = agent_execution_map[agent_type]
            agent_status = AgentExecutionStatus(
                agent_name=agent_type.title() + " Agent",
                status="executing",
                description="Processing query",
                start_time=datetime.now()
            )
            update_agent_status(session_id, agent_status)

            result = await execute_func(query_interpretation, query_interpretation, session_id)
            agent_result_content = result.result
            agent_status.description = f"Agent {agent_type} completed processing."
            agent_status.status = "completed"
            agent_status.result = agent_result_content
            agent_status.end_time = datetime.now()
            update_agent_status(session_id, agent_status)

            all_agent_results.append(agent_status)
            # Accumulate textual results for final synthesis
            if isinstance(agent_result_content, dict) and "summary" in agent_result_content:
                 final_response_parts.append(str(agent_result_content["summary"]))
            elif isinstance(agent_result_content, dict) and "content" in agent_result_content:
                 final_response_parts.append(str(agent_result_content["content"]))
            elif isinstance(agent_result_content, str):
                final_response_parts.append(agent_result_content)
            else: # Fallback for other types of results
                final_response_parts.append(json.dumps(convert_numpy_types(agent_result_content), indent=2))

        except Exception as e:
            print(f"Error executing agent {agent_type}: {e}")
            agent_status.status = "failed"
            agent_status.error = str(e)
            agent_status.end_time = datetime.now()
            update_agent_status(session_id, agent_status)
            all_agent_results.append(agent_status)
            final_response_parts.append(f"Error with {agent_type}: {e}")

    update_execution_status(session_id, "Synthesizing Response", "executing", 80.0)
    
    # Synthesize final response
    if not final_response_parts:
        final_summary = "I could not find specific information for your query. Please try rephrasing or be more specific."
    elif len(final_response_parts) == 1:
        final_summary = final_response_parts[0]
    else:
        synthesis_prompt = (
            f"The user asked: '{query_interpretation}'. Multiple AI agents have processed this query. "
            "Their findings are summarized below. Your task is to synthesize these findings into a single, coherent, "
            "and easy-to-understand response for the user. Ensure the response directly addresses the user's original query. "
            "Present the information clearly. If there are multiple pieces of information, structure them logically. "
            "Do not just list the findings; integrate them. Here are the findings:\\n\\n"
            + "\\n\\n---\\n\\n".join(final_response_parts)
            + "\\n\\nSynthesized Response:"
        )
        try:
            final_summary = await language_agent_instance.generate_response_async(synthesis_prompt, max_tokens=1024)
        except Exception as e:
            print(f"Error during final synthesis: {e}")
            final_summary = "I gathered some information, but had trouble putting it all together. Here are the raw findings:\\n" + "\\n".join(final_response_parts)

    update_execution_status(session_id, "Finalizing", "completed", 90.0)

    wav_audio_base64 = None
    if voice_mode:
        try:
            # Use the main voice agent for TTS
            temp_audio_path = voice_agent_instance.text_to_speech(final_summary, output_filename="orchestrator_tts_output.wav")
            if temp_audio_path and os.path.exists(temp_audio_path):
                    with open(temp_audio_path, "rb") as wav_file:
                        wav_audio_base64 = base64.b64encode(wav_file.read()).decode()
                    os.remove(temp_audio_path) # Clean up temp file
                    update_execution_status(session_id, "Generated Voice Output", "completed", 95.0)
        except Exception as e:
                print(f"Error generating TTS: {e}")
                # Proceed without audio if TTS fails

    final_response = IntelligentResponse(
        response_text=final_summary.strip(),
        agents_used=all_agent_results,
            query_interpretation=query_interpretation,
        wav_audio_base64=wav_audio_base64,
            confidence=confidence,
            session_id=session_id
        )
    update_execution_status(session_id, "Response Ready", "completed", 100.0)
    return final_response

def process_intelligent_query_sync(query: str, voice_mode: bool = False, include_debug: bool = False) -> IntelligentResponse:
    """Synchronous wrapper for process_intelligent_query.
    This is what Streamlit will call if it cannot easily manage async calls.
    """
    import asyncio
    try:
        # Check if there's an existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If a loop is running, create a new task
            # This might be an issue in some environments like Streamlit that manage their own loop.
            # For simplicity, we'll try to run it in a new loop if possible, or directly if not.
            # A more robust solution might involve `nest_asyncio` or a dedicated thread for the async loop.
            return asyncio.run(process_intelligent_query(query, voice_mode, include_debug))
        else:
            return loop.run_until_complete(process_intelligent_query(query, voice_mode, include_debug))
    except RuntimeError as e: # Handles "no event loop" or "event loop is closed"
        # If no loop or loop is closed, create a new one
        return asyncio.run(process_intelligent_query(query, voice_mode, include_debug))

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
async def get_agent_status_endpoint(): # Renamed to avoid conflict with the direct-callable function
    """
    Provides the current status and configuration of all available agents. (API Endpoint)
    """
    agents = _initialized_agents if _initialized_agents else initialize_agents() # Ensure agents are initialized

    return {
        "orchestrator_version": app.version,
        "language_model": agents["language_agent"].model_name,
        "available_agents": [
            {"name": "Voice Agent", "status": "active" if agents.get("voice_agent") else "inactive", "details": agents["voice_agent"].get_status() if agents.get("voice_agent") else {}},
            {"name": "Retriever Agent", "status": "active" if agents.get("retriever_agent") else "inactive", "details": agents["retriever_agent"].get_status() if agents.get("retriever_agent") else {}},
            {"name": "Analysis Agent", "status": "active" if agents.get("analysis_agent") else "inactive", "details": agents["analysis_agent"].get_status() if agents.get("analysis_agent") else {}},
            {"name": "Language Agent", "status": "active" if agents.get("language_agent") else "inactive", "details": agents["language_agent"].get_status() if agents.get("language_agent") else {}},
            {"name": "Market Agent", "status": "active" if agents.get("market_agent") else "inactive", "details": agents["market_agent"].get_status() if agents.get("market_agent") else {}},
            {"name": "Scraping Agent", "status": "active" if agents.get("scraping_agent") else "inactive", "details": agents["scraping_agent"].get_status() if agents.get("scraping_agent") else {}}
        ]
    }

def get_agent_status(): # Direct-callable function for Streamlit
    """
    Provides the current status and configuration of all available agents. (Direct Call)
    """
    agents = _initialized_agents if _initialized_agents else initialize_agents() # Ensure agents are initialized
    # Ensure MISTRAL_API_KEY is available for LanguageAgent
    if "MISTRAL_API_KEY" not in os.environ:
        # Attempt to get it from streamlit secrets if available, otherwise raise error or use a default
        # This part depends on how Streamlit secrets are structured and if they are available here.
        # For now, we assume it's set as an environment variable.
        # A more robust solution would be to pass config explicitly or use a shared config module.
        print("Warning: MISTRAL_API_KEY not found in environment. Language agent might fail.")


    language_agent_instance = agents.get("language_agent")
    
    return {
        "orchestrator_version": "2.0.0", # app.version might not be available if FastAPI app is not fully run
        "language_model": language_agent_instance.model_name if language_agent_instance else "N/A",
        "available_agents": [
            {"name": "Voice Agent", "status": "active" if agents.get("voice_agent") else "inactive", "details": agents["voice_agent"].get_status() if agents.get("voice_agent") else {}},
            {"name": "Retriever Agent", "status": "active" if agents.get("retriever_agent") else "inactive", "details": agents["retriever_agent"].get_status() if agents.get("retriever_agent") else {}},
            {"name": "Analysis Agent", "status": "active" if agents.get("analysis_agent") else "inactive", "details": agents["analysis_agent"].get_status() if agents.get("analysis_agent") else {}},
            {"name": "Language Agent", "status": "active" if language_agent_instance else "inactive", "details": language_agent_instance.get_status() if language_agent_instance else {}},
            {"name": "Market Agent", "status": "active" if agents.get("market_agent") else "inactive", "details": agents["market_agent"].get_status() if agents.get("market_agent") else {}},
            {"name": "Scraping Agent", "status": "active" if agents.get("scraping_agent") else "inactive", "details": agents["scraping_agent"].get_status() if agents.get("scraping_agent") else {}}
        ]
    }

# Ensure agents are initialized when the FastAPI app starts (for API endpoints)
@app.on_event("startup")
async def startup_event():
    initialize_agents()

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