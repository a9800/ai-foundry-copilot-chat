from os import environ
import logging
from microsoft_agents.hosting.core import AgentApplication, AgentAuthConfiguration
from microsoft_agents.hosting.aiohttp import (
    start_agent_process,
    jwt_authorization_middleware,
    CloudAdapter,
)
from aiohttp.web import Request, Response, Application, run_app

# Set up logging
logger = logging.getLogger(__name__)

def start_server(
    agent_application: AgentApplication, auth_configuration: AgentAuthConfiguration
):
    async def entry_point(req: Request) -> Response:
        # Log incoming requests
        logger.info(f"Received request: {req.method} {req.path}")
        logger.info(f"Headers: {dict(req.headers)}")
        logger.info(f"Remote: {req.remote}")
        
        agent: AgentApplication = req.app["agent_app"]
        adapter: CloudAdapter = req.app["adapter"]
        
        try:
            response = await start_agent_process(req, agent, adapter)
            logger.info(f"Response status: {response.status}")
            return response
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            raise

    # Check if we're in development mode (for Teams App Test Tool)
    is_development = environ.get("DEVELOPMENT_MODE", "false").lower() == "true"
    print("DEV MODE: ", is_development)
    
    if is_development:
        # No authentication middleware for local testing
        APP = Application()
    else:
        # Use JWT authentication for production/Azure
        APP = Application(middlewares=[jwt_authorization_middleware])
    
    APP.router.add_post("/api/messages", entry_point)
    APP["agent_configuration"] = auth_configuration
    APP["agent_app"] = agent_application
    APP["adapter"] = agent_application.adapter

    try:
        run_app(APP, host="localhost", port=environ.get("PORT", 3978))
    except Exception as error:
        raise error