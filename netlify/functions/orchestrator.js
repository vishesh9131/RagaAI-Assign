const axios = require('axios');

exports.handler = async (event, context) => {
  // Set CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
    'Content-Type': 'application/json'
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  try {
    const path = event.path.replace('/.netlify/functions/orchestrator', '');
    
    // Agents status endpoint
    if (event.httpMethod === 'GET' && path === '/agents/status') {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          status: 'healthy',
          service: 'AI Financial Assistant Orchestrator',
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          available_agents: [
            {
              name: 'Financial Analysis Agent',
              status: 'active',
              capabilities: ['market analysis', 'stock prices', 'portfolio management']
            },
            {
              name: 'Investment Strategy Agent', 
              status: 'active',
              capabilities: ['investment advice', 'risk analysis', 'diversification']
            },
            {
              name: 'Market Data Agent',
              status: 'active',
              capabilities: ['real-time data', 'historical trends', 'market news']
            }
          ]
        })
      };
    }

    // Health check endpoint (backward compatibility)
    if (event.httpMethod === 'GET' && path === '/health') {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          status: 'healthy',
          service: 'AI Financial Assistant Orchestrator',
          timestamp: new Date().toISOString(),
          version: '1.0.0'
        })
      };
    }

    // Intelligent query endpoint
    if (event.httpMethod === 'POST' && path === '/intelligent/query') {
      const body = JSON.parse(event.body || '{}');
      const { query, voice_mode = false } = body;

      if (!query) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Query is required' })
        };
      }

      // Enhanced response logic based on query content
      let response = "I'm here to help with your financial questions.";
      let confidence = 0.85;
      
      if (query.toLowerCase().includes('stock') || query.toLowerCase().includes('aapl') || query.toLowerCase().includes('price')) {
        response = "Based on current market analysis, I can help you with stock information. For real-time data, I recommend checking the latest market feeds. This is a demo response showing how the AI would process stock-related queries.";
        confidence = 0.92;
      } else if (query.toLowerCase().includes('invest') || query.toLowerCase().includes('portfolio')) {
        response = "For investment strategies, I recommend considering a diversified portfolio approach. Key factors include risk tolerance, time horizon, and financial goals. This demo shows how I would analyze investment queries.";
        confidence = 0.88;
      } else if (query.toLowerCase().includes('market') || query.toLowerCase().includes('trend')) {
        response = "Current market trends show various patterns across different sectors. I can analyze market conditions and provide insights based on historical data and current indicators. This is a sample market analysis response.";
        confidence = 0.90;
      }

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          response: response,
          confidence: confidence,
          timestamp: new Date().toISOString(),
          model: 'demo-financial-assistant',
          query_type: 'intelligent',
          voice_mode: voice_mode
        })
      };
    }

    // Voice endpoint 
    if (event.httpMethod === 'POST' && path === '/intelligent/voice') {
      const body = JSON.parse(event.body || '{}');
      const { query, audio_data } = body;

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          response: "Voice processing is currently limited in serverless environments. For full voice capabilities, please use the Streamlit app. This query has been processed as text: " + (query || "No query provided"),
          confidence: 0.75,
          timestamp: new Date().toISOString(),
          model: 'demo-voice-assistant',
          query_type: 'voice',
          limitation: 'Serverless voice processing is limited'
        })
      };
    }

    // Chat endpoint (backward compatibility)
    if (event.httpMethod === 'POST' && path === '/chat') {
      const body = JSON.parse(event.body || '{}');
      const { message, history = [] } = body;

      if (!message) {
        return {
          statusCode: 400,
          headers,
          body: JSON.stringify({ error: 'Message is required' })
        };
      }

      const responses = [
        "I'm here to help with your financial questions. As a demo response, I can assist with market analysis, investment strategies, and financial planning.",
        "Based on current market trends, here are some insights for your financial portfolio...",
        "Let me analyze that financial data for you. This is a sample response from the AI assistant.",
        "For your investment query, I recommend considering diversified portfolio strategies..."
      ];

      const randomResponse = responses[Math.floor(Math.random() * responses.length)];

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          response: randomResponse,
          confidence: 0.85,
          timestamp: new Date().toISOString(),
          model: 'demo-mode'
        })
      };
    }

    // Default 404 for unknown endpoints
    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ 
        error: 'Endpoint not found',
        available_endpoints: [
          'GET /api/agents/status',
          'GET /api/health', 
          'POST /api/intelligent/query',
          'POST /api/intelligent/voice',
          'POST /api/chat'
        ]
      })
    };

  } catch (error) {
    console.error('Function error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'Internal server error',
        message: error.message 
      })
    };
  }
}; 