import json
import os
from datetime import datetime
import logging

def handler(event, context):
    """
    Netlify Functions handler for orchestrator API
    """
    try:
        # Enable CORS for all requests
        cors_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE'
        }
        
        # Handle preflight requests
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': ''
            }
        
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        # Handle different API endpoints
        if path.endswith('/agents/status') or 'agents' in path:
            return handle_agents_status(cors_headers)
        elif path.endswith('/intelligent/query') or 'query' in path:
            body = json.loads(event.get('body', '{}'))
            return handle_intelligent_query(body, cors_headers)
        elif path.endswith('/intelligent/voice') or 'voice' in path:
            return handle_voice_query(event, cors_headers)
        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({'error': 'Endpoint not found', 'path': path})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e), 'type': 'server_error'})
        }

def handle_agents_status(headers):
    """Handle agents status endpoint"""
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'available_agents': [
                {
                    'name': 'Market Agent',
                    'description': 'Stock prices, company info, earnings data',
                    'status': 'active'
                },
                {
                    'name': 'Analysis Agent',
                    'description': 'Portfolio analysis, sentiment analysis, market trends',
                    'status': 'active'
                },
                {
                    'name': 'Language Agent',
                    'description': 'Text processing and explanation powered by Mistral AI',
                    'status': 'active'
                },
                {
                    'name': 'Retriever Agent',
                    'description': 'Document search and retrieval',
                    'status': 'active'
                },
                {
                    'name': 'Scraping Agent',
                    'description': 'Web content extraction',
                    'status': 'active'
                },
                {
                    'name': 'Voice Agent',
                    'description': 'Speech-to-text and text-to-speech',
                    'status': 'active'
                }
            ],
            'orchestrator_version': '3.0.0',
            'language_model': 'Mistral AI open-mistral-nemo',
            'active_sessions': 0,
            'deployment': 'netlify_serverless'
        })
    }

def handle_intelligent_query(body, headers):
    """Handle intelligent query processing"""
    query = body.get('query', '')
    voice_mode = body.get('voice_mode', False)
    include_debug = body.get('include_debug_info', False)
    
    # Get environment variables
    mistral_api_key = os.environ.get('MISTRAL_API_KEY')
    
    if not mistral_api_key:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Mistral API key not configured',
                'response_text': 'Sorry, the AI service is not configured properly. Please contact the administrator.'
            })
        }
    
    try:
        # Simple response for now - you can integrate actual Mistral AI processing here
        # For a more complete implementation, you would:
        # 1. Initialize Mistral client with API key
        # 2. Process the query through appropriate agents
        # 3. Return formatted response
        
        # Simulate processing time and response
        import time
        start_time = time.time()
        
        # Basic query processing (replace with actual AI logic)
        response_text = generate_mock_response(query)
        
        processing_time = time.time() - start_time
        
        response_data = {
            'response_text': response_text,
            'confidence': 0.85,
            'session_id': f"netlify_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'agents_used': [
                {
                    'agent_name': 'Language Agent',
                    'status': 'completed',
                    'description': 'Processed natural language query using Mistral AI',
                    'start_time': datetime.now().isoformat(),
                    'end_time': datetime.now().isoformat()
                }
            ],
            'query_interpretation': f'Interpreted as financial query about: {extract_topic(query)}',
            'routing_info': {
                'primary_agent': 'Language Agent',
                'processing_time': processing_time
            },
            'wav_audio_base64': None  # Voice not implemented in serverless yet
        }
        
        if include_debug:
            response_data['debug_info'] = {
                'deployment': 'netlify_serverless',
                'function_name': 'orchestrator',
                'environment': 'production'
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': f'Query processing failed: {str(e)}',
                'response_text': 'I apologize, but I encountered an error processing your request. Please try again.',
                'confidence': 0.0
            })
        }

def handle_voice_query(event, headers):
    """Handle voice query processing"""
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'response_text': 'Voice processing is currently not available in the serverless deployment. Please use text input.',
            'confidence': 0.5,
            'session_id': f"voice_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'agents_used': [],
            'error': 'Voice processing not implemented in serverless mode'
        })
    }

def generate_mock_response(query):
    """Generate a mock response based on the query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['stock', 'price', 'aapl', 'tsla', 'market']):
        return f"I understand you're asking about stock market information: '{query}'. In a full deployment, I would provide real-time stock data, analysis, and market insights using multiple AI agents working together."
    
    elif any(word in query_lower for word in ['portfolio', 'investment', 'analyze']):
        return f"You're asking about portfolio or investment analysis: '{query}'. The full system would analyze your portfolio, provide risk assessments, and offer personalized investment recommendations based on current market conditions."
    
    elif any(word in query_lower for word in ['news', 'trend', 'economic']):
        return f"You're interested in financial news or economic trends: '{query}'. The complete system would gather the latest financial news, analyze market trends, and provide comprehensive economic insights."
    
    else:
        return f"I received your financial query: '{query}'. This is a demo response from the serverless deployment. In the full system, multiple AI agents would collaborate to provide detailed financial analysis, market data, and personalized insights."

def extract_topic(query):
    """Extract the main topic from the query"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['stock', 'share', 'equity']):
        return 'stock market'
    elif any(word in query_lower for word in ['portfolio', 'investment']):
        return 'portfolio management'
    elif any(word in query_lower for word in ['news', 'headline']):
        return 'financial news'
    elif any(word in query_lower for word in ['trend', 'analysis', 'market']):
        return 'market analysis'
    else:
        return 'general financial inquiry' 