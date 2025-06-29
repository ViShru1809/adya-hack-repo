import logging
from collections.abc import Sequence
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, Optional
import traceback
from dotenv import load_dotenv
from mcp.types import Tool
import json
from mcp_gsuite import gauth
from mcp_gsuite import tools_gmail
from mcp_gsuite import tools_calendar
from mcp_gsuite import toolhandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-gsuite")

app = FastAPI()

# Allow CORS for all origins (adjust as necessary)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tool Handlers Registry
tool_handlers: Dict[str, toolhandler.ToolHandler] = {}


def setup_oauth2(user_id: str):
    """Setup OAuth2 credentials for a given user."""
    try:
        accounts = gauth.get_account_info()
        if len(accounts) == 0:
            raise HTTPException(
                status_code=400, 
                detail="No accounts specified in .gauth.json"
            )
        if user_id not in [a.email for a in accounts]:
            raise HTTPException(
                status_code=400,
                detail=f"Account for email: {user_id} not specified in .gauth.json"
            )

        credentials = gauth.get_stored_credentials(user_id=user_id)
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="OAuth2 credentials not found. Authentication required."
            )
        
        user_info = gauth.get_user_info(credentials=credentials)
        gauth.store_credentials(credentials=credentials, user_id=user_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Authentication configuration file (.gauth.json) not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication setup failed: {str(e)}"
        )


@app.post("/call_tool/")
async def call_tool(payload: dict):
    try:
        name = payload.get("name")
        arguments = payload.get("arguments")
        
        logger.info(f"Received tool call: {name}")
        logger.info(f"Payload arguments: {arguments}")

        # Ensure the payload matches expectations
        if not isinstance(arguments, dict):
            raise HTTPException(status_code=400, detail="Arguments must be a dictionary.")
        if toolhandler.USER_ID_ARG not in arguments:
            raise HTTPException(status_code=400, detail="Missing '__user_id__' in arguments.")

        # Proceed with tool execution
        setup_oauth2(user_id=arguments[toolhandler.USER_ID_ARG])
        tool_handler = get_tool_handler(name)
        if not tool_handler:
            raise HTTPException(status_code=404, detail=f"Tool '{name}' not found.")
        return tool_handler.run_tool(arguments)
    except Exception as e:
        logger.error(f"Error in call_tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_tools/")
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [th.get_tool_description() for th in tool_handlers.values()]


def add_tool_handler(tool_class: toolhandler.ToolHandler):
    """Register a tool handler."""
    global tool_handlers
    tool_handlers[tool_class.name] = tool_class


def get_tool_handler(name: str) -> Optional[toolhandler.ToolHandler]:
    """Retrieve a tool handler by name."""
    return tool_handlers.get(name)


@app.on_event("startup")
async def startup_event():
    """Register all tool handlers on startup."""
    # Gmail tools
    add_tool_handler(tools_gmail.QueryEmailsToolHandler())
    add_tool_handler(tools_gmail.GetEmailByIdToolHandler())
    add_tool_handler(tools_gmail.CreateDraftToolHandler())
    add_tool_handler(tools_gmail.DeleteDraftToolHandler())
    add_tool_handler(tools_gmail.ReplyEmailToolHandler())
    add_tool_handler(tools_gmail.GetAttachmentToolHandler())
    add_tool_handler(tools_gmail.BulkGetEmailsByIdsToolHandler())
    add_tool_handler(tools_gmail.BulkSaveAttachmentsToolHandler())

    # Calendar tools
    add_tool_handler(tools_calendar.ListCalendarsToolHandler())
    add_tool_handler(tools_calendar.GetCalendarEventsToolHandler())
    add_tool_handler(tools_calendar.CreateCalendarEventToolHandler())
    add_tool_handler(tools_calendar.DeleteCalendarEventToolHandler())
