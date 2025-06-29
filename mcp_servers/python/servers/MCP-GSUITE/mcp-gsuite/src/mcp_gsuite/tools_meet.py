from collections.abc import Sequence
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from . import toolhandler
from . import meet
import json

class CreateMeetingToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("create_meet_meeting")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Creates a new Google Meet meeting and returns the meeting details including the join link. ",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Title of the meeting"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description or agenda for the meeting (optional)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g. 2024-12-01T10:00:00Z -> 2024-12-01 10:00:00)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time in RFC3339 format (e.g. 2024-12-01T11:00:00Z -> 2024-12-01 11:00:00)"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of attendee email addresses (optional)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the meeting (e.g. 'America/New_York'). Defaults to UTC if not specified."
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["summary", "start_time", "end_time"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        # user_id = args.get(toolhandler.USER_ID_ARG)
        # if not user_id:
        #     raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        credentials = args.get(toolhandler.CREDENTIALS_ARG)
        if not credentials:
            raise RuntimeError(f"Missing required argument: {toolhandler.CREDENTIALS_ARG}")

        meet_service = meet.MeetService(credentials=credentials)
        meeting = meet_service.create_meeting(
            summary=args["summary"],
            start_time=args["start_time"],
            end_time=args["end_time"],
            description=args.get("description"),
            attendees=args.get("attendees", []),
            timezone=args.get("timezone"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(meeting, indent=2)
            )
        ]

class CancelMeetingToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("cancel_meet_meeting")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Cancels an existing Google Meet meeting. if you need event id use get_all_meet_meetings with the start time and end time of the meeting to get the event id",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the meeting/event to cancel"
                   
                    }
                },
                "required": ["event_id"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        if "event_id" not in args:
            raise RuntimeError("Missing required argument: event_id")

        # user_id = args.get(toolhandler.USER_ID_ARG)
        # if not user_id:
        #     raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        credentials = args.get(toolhandler.CREDENTIALS_ARG)
        if not credentials:
            raise RuntimeError(f"Missing required argument: {toolhandler.CREDENTIALS_ARG}")

        meet_service = meet.MeetService(credentials=credentials)
        success = meet_service.cancel_meeting(event_id=args["event_id"])

        return [
            TextContent(
                type="text",
                text=json.dumps({"success": success}, indent=2)
            )
        ]

class RescheduleMeetingToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("reschedule_meet_meeting")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Reschedules an existing Google Meet meeting to a new time. if you need event id use get_all_meet_meetings with the start time and end time of the meeting to get the event id",
            inputSchema={
                "type": "object",
                "properties": {
     
                    "event_id": {
                        "type": "string",
                        "description": "The ID of the meeting/event to reschedule"
                    },
                    "new_start_time": {
                        "type": "string",
                        "description": "New start time in RFC3339 format (e.g. 2024-12-01T10:00:00Z)"
                    },
                    "new_end_time": {
                        "type": "string",
                        "description": "New end time in RFC3339 format (e.g. 2024-12-01T11:00:00Z)"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone for the meeting (e.g. 'America/New_York'). Defaults to UTC if not specified."
                    
                    }
                },
                "required": [ "event_id", "new_start_time", "new_end_time"]
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        required = ["event_id", "new_start_time", "new_end_time"]
        if not all(key in args for key in required):
            raise RuntimeError(f"Missing required arguments: {', '.join(required)}")

        # user_id = args.get(toolhandler.USER_ID_ARG)
        # if not user_id:
        #     raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        credentials = args.get(toolhandler.CREDENTIALS_ARG)
        if not credentials:
            raise RuntimeError(f"Missing required argument: {toolhandler.CREDENTIALS_ARG}")

        meet_service = meet.MeetService(credentials=credentials)
        updated_meeting = meet_service.reschedule_meeting(
            event_id=args["event_id"],
            new_start_time=args["new_start_time"],
            new_end_time=args["new_end_time"],
            timezone=args.get("timezone"),
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(updated_meeting, indent=2)
            )
        ]

class GetAllMeetingsToolHandler(toolhandler.ToolHandler):
    def __init__(self):
        super().__init__("get_all_meet_meetings")

    def get_tool_description(self) -> Tool:
        return Tool(
            name=self.name,
            description="Retrieves all Google Meet meetings from the calendar within a specified time range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Start time in RFC3339 format (e.g. 2024-12-01T00:00:00Z). Defaults to current time if not specified."
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End time in RFC3339 format (e.g. 2024-12-31T23:59:59Z). Optional."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of meetings to return",
                        "default": 100,
                        "minimum": 1
                    },
                    "include_past": {
                        "type": "boolean",
                        "description": "Whether to include past meetings",
                        "default": False
                    
                    }
                },
            }
        )

    def run_tool(self, args: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        # user_id = args.get(toolhandler.USER_ID_ARG)
        # if not user_id:
        #     raise RuntimeError(f"Missing required argument: {toolhandler.USER_ID_ARG}")

        credentials = args.get(toolhandler.CREDENTIALS_ARG)
        if not credentials:
            raise RuntimeError(f"Missing required argument: {toolhandler.CREDENTIALS_ARG}")

        meet_service = meet.MeetService(credentials=credentials)
        meetings = meet_service.get_all_meetings(
            time_min=args.get("time_min"),
            time_max=args.get("time_max"),
            max_results=args.get("max_results", 100),
            include_past=args.get("include_past", False)
        )

        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "total_meetings": len(meetings),
                    "meetings": meetings
                }, indent=2)
            )
        ]