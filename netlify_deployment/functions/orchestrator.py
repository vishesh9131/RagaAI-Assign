import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required environment variables
os.environ.setdefault("MISTRAL_API_KEY", "NxdIH9V8xm8eldEGZrKvC1M1ziS1jHal")

try:
    # Import the FastAPI app
    from orchestrator.orchestrator_fastapi import app, initialize_agents
    from mangum import Mangum
    
    # Initialize agents on cold start
    print("Initializing AI Financial Assistant agents...")
    agents = initialize_agents()
    print(f"Successfully initialized {len(agents)} agents: {list(agents.keys())}")
    
    # Create the Mangum handler
    handler = Mangum(app, lifespan="off")
    
    def netlify_handler(event, context):
        """Netlify function handler."""
        try:
            # Convert Netlify event to ASGI format
            response = handler(event, context)
            return response
        except Exception as e:
            print(f"Error in netlify_handler: {e}")
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Internal server error",
                    "message": str(e)
                })
            }

except ImportError as e:
    print(f"Failed to import orchestrator: {e}")
    
    # Fallback function if import fails
    def netlify_handler(event, context):
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Import error",
                "message": f"Failed to load orchestrator: {str(e)}"
            })
        } 