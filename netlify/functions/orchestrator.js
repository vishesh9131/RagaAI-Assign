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
    
    // Health check endpoint
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

    // Chat endpoint
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

      // Simple response logic (you can replace this with actual AI integration)
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
      body: JSON.stringify({ error: 'Endpoint not found' })
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