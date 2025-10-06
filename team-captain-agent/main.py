from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastMCP()


# Models for tool inputs/outputs
class SchedulePhotoData(BaseModel):
    team_id: int
    file_content: str  # base64 encoded
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: str


class ScheduleData(BaseModel):
    schedule_content: str
    team_id: str


class ReminderData(BaseModel):
    message: str
    recipients: List[str]
    team_id: str


class AttendanceData(BaseModel):
    attendance_records: List[Dict[str, Any]]
    team_id: str


@app.tool()
async def process_schedule_photo(data: SchedulePhotoData) -> Dict[str, Any]:
    """
    Process uploaded schedule photo. Main orchestrator tool called by Laravel.
    
    This tool:
    1. Receives photo from Laravel
    2. Delegates to Schedule Agent for AI analysis
    3. Coordinates event creation back to Laravel
    4. Returns structured results
    """
    try:
        logger.info(f"Processing schedule photo for team {data.team_id}")
        logger.info(f"File: {data.file_name}, Size: {data.file_size}, Type: {data.mime_type}")

        # Step 1: Call Schedule Agent to analyze the image
        schedule_analysis = await call_schedule_agent_analyze_image(data)
        
        if not schedule_analysis.get("success", False):
            logger.error(f"Schedule analysis failed: {schedule_analysis}")
            return {
                "success": False,
                "message": "Failed to analyze schedule image",
                "error": schedule_analysis.get("error", "Unknown error"),
                "team_id": data.team_id
            }

        events = schedule_analysis.get("events", [])
        logger.info(f"Schedule analysis found {len(events)} events")

        # Step 2: Call Schedule Agent to create events in Laravel database
        if events:
            event_creation = await call_schedule_agent_create_events({
                "team_id": data.team_id,
                "events": events
            })
            
            if not event_creation.get("success", False):
                logger.error(f"Event creation failed: {event_creation}")
                return {
                    "success": False,
                    "message": "Failed to create events from schedule",
                    "error": event_creation.get("error", "Unknown error"),
                    "parsed_events": events,
                    "team_id": data.team_id
                }
        else:
            event_creation = {"success": True, "events_created": 0}

        # Step 3: Return comprehensive results
        return {
            "success": True,
            "message": f"Schedule processed successfully - {len(events)} events found",
            "analysis_results": {
                "events_found": len(events),
                "events_created": event_creation.get("events_created", 0),
                "file_processed": data.file_name,
                "file_size": data.file_size,
                "processing_completed_at": data.uploaded_at
            },
            "parsed_events": events,
            "team_id": data.team_id
        }

    except Exception as e:
        logger.error(f"Error in process_schedule_photo: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to process schedule photo: {str(e)}",
            "team_id": data.team_id
        }


async def call_schedule_agent_analyze_image(data: SchedulePhotoData) -> Dict[str, Any]:
    """
    Call Schedule Agent's analyze_schedule_image tool via MCP.
    """
    try:
        # For now, we'll use HTTP until we implement MCP client-to-client communication
        # TODO: Replace with proper MCP client call
        
        schedule_agent_url = "http://schedule-agent:8000"
        
        payload = {
            "team_id": data.team_id,
            "file_content": data.file_content,
            "file_name": data.file_name,
            "file_size": data.file_size,
            "mime_type": data.mime_type,
            "uploaded_at": data.uploaded_at
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{schedule_agent_url}/tools/analyze_schedule_image",
                json=payload
            )
            
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully called Schedule Agent for image analysis")
            return result
        else:
            logger.error(f"Schedule Agent call failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error calling Schedule Agent: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


async def call_schedule_agent_create_events(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Schedule Agent's create_events tool via MCP.
    """
    try:
        schedule_agent_url = "http://schedule-agent:8000"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{schedule_agent_url}/tools/create_events",
                json=data
            )
            
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully called Schedule Agent for event creation")
            return result
        else:
            logger.error(f"Event creation call failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error calling Schedule Agent for event creation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.tool()
async def upload_schedule(data: ScheduleData) -> Dict[str, Any]:
    """
    Upload and parse a team schedule. Delegates to Schedule Agent.
    """
    # TODO: Implement MCP client call to Schedule Agent
    return {
        "success": True,
        "message": "Schedule uploaded successfully",
        "parsed_events": [],
        "team_id": data.team_id,
    }


@app.tool()
async def send_reminder(data: ReminderData) -> Dict[str, Any]:
    """
    Send a reminder to team members. Orchestrates multiple agents.
    """
    # TODO: Implement reminder logic with multiple agents
    return {
        "success": True,
        "message": "Reminder sent successfully",
        "recipients": data.recipients,
        "team_id": data.team_id,
    }


@app.tool()
async def analyze_attendance(data: AttendanceData) -> Dict[str, Any]:
    """
    Analyze attendance patterns. Delegates to Attendance Agent.
    """
    # TODO: Implement MCP client call to Attendance Agent
    return {
        "success": True,
        "message": "Attendance analysis completed",
        "patterns": {},
        "team_id": data.team_id,
    }




if __name__ == "__main__":
    # Check if we need to run as web server
    import os
    if os.getenv("RUN_HTTP", "false").lower() == "true":
        logger.info("Starting as HTTP server using uvicorn")
        import uvicorn
        # FastMCP should integrate with ASGI
        try:
            # Try to get ASGI app from FastMCP
            asgi_app = getattr(app, 'app', None) or getattr(app, '_app', None)
            if asgi_app:
                uvicorn.run(asgi_app, host="0.0.0.0", port=8000)
            else:
                logger.error("Could not get ASGI app from FastMCP")
                app.run()
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            app.run()
    else:
        logger.info("Starting with STDIO transport")
        app.run()
