from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Dict, Any, List
import base64
import logging
import json
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP app
app = FastMCP()


# Models for tool inputs/outputs
class ScheduleImageAnalysisRequest(BaseModel):
    team_id: int
    file_content: str  # base64 encoded file content
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: str


class EventCreationRequest(BaseModel):
    team_id: int
    events: List[Dict[str, Any]]


class ScheduleEvent(BaseModel):
    event_id: str
    title: str
    date: str
    time: str
    location: str
    team_id: str
    type: str = "practice"
    opponent: str = None


@app.tool()
async def analyze_schedule_image(data: ScheduleImageAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze schedule image using LLM to extract structured events.
    
    This tool:
    1. Decodes the base64 image
    2. Sends image to LLM with schedule extraction prompt
    3. Parses LLM response into structured events
    4. Returns events ready for database creation
    """
    try:
        logger.info(f"Starting schedule image analysis for team {data.team_id}")
        logger.info(f"File: {data.file_name}, Size: {data.file_size}, Type: {data.mime_type}")

        # Decode the base64 file content
        try:
            file_content = base64.b64decode(data.file_content)
            logger.info(f"Successfully decoded file content, size: {len(file_content)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {e}")
            return {
                "success": False,
                "message": "Failed to decode uploaded file",
                "error": str(e),
            }

        # TODO: Implement actual LLM analysis
        # For now, we'll return mock events that match your Event model structure
        logger.info(f"Analyzing schedule image for team {data.team_id}")
        
        # Call LLM analysis (placeholder)
        analysis_results = await call_llm_for_schedule_analysis(file_content, data.mime_type)
        
        if not analysis_results.get("success", False):
            return analysis_results

        events = analysis_results.get("events", [])
        logger.info(f"LLM analysis found {len(events)} events")

        return {
            "success": True,
            "message": f"Schedule image analyzed successfully - {len(events)} events found",
            "events": events,
            "total_events": len(events),
            "team_id": data.team_id,
            "file_processed": data.file_name,
            "processed_at": datetime.now().isoformat(),
            "analysis_method": "llm_vision"
        }

    except Exception as e:
        logger.error(f"Error analyzing schedule image: {e}", exc_info=True)
        return {
            "success": False,
            "message": "Failed to analyze schedule image",
            "error": str(e),
            "team_id": data.team_id,
        }


async def call_llm_for_schedule_analysis(file_content: bytes, mime_type: str) -> Dict[str, Any]:
    """
    Call LLM to analyze schedule image and extract events.
    """
    try:
        # TODO: Replace with actual LLM API call (OpenAI, Anthropic, etc.)
        # For now, return mock structured events
        
        logger.info("Calling LLM for schedule analysis (mock implementation)")
        
        # Mock events that match Laravel Event model structure
        mock_events = [
            {
                "title": "Team Practice",
                "date": "2025-01-15",
                "time": "18:00:00",
                "location": "Main Field",
                "type": "practice",
                "description": "Regular team practice session"
            },
            {
                "title": "Home Game vs Eagles",
                "date": "2025-01-22",
                "time": "19:00:00", 
                "location": "Stadium",
                "type": "game",
                "description": "Home game against Eagles"
            },
            {
                "title": "Away Game vs Panthers",
                "date": "2025-01-29",
                "time": "17:30:00",
                "location": "Panthers Stadium", 
                "type": "game",
                "description": "Away game against Panthers"
            }
        ]
        
        return {
            "success": True,
            "events": mock_events,
            "analysis_confidence": 0.95
        }
        
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@app.tool()
async def create_events(data: EventCreationRequest) -> Dict[str, Any]:
    """
    Create events in Laravel database via HTTP API.
    
    This tool:
    1. Receives structured events from Team Captain
    2. Makes HTTP calls to Laravel to create each event
    3. Returns creation results and statistics
    """
    try:
        logger.info(f"Creating {len(data.events)} events for team {data.team_id}")
        
        created_events = []
        failed_events = []
        
        for event_data in data.events:
            try:
                # Add team_id to event data
                event_data['team_id'] = data.team_id
                
                # Call Laravel API to create event
                result = await call_laravel_create_event(event_data)
                
                if result.get("success", False):
                    created_events.append(result.get("event"))
                    logger.info(f"Successfully created event: {event_data.get('title', 'Unknown')}")
                else:
                    failed_events.append({
                        "event_data": event_data,
                        "error": result.get("error", "Unknown error")
                    })
                    logger.error(f"Failed to create event: {event_data.get('title', 'Unknown')} - {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Exception creating event {event_data.get('title', 'Unknown')}: {e}")
                failed_events.append({
                    "event_data": event_data,
                    "error": str(e)
                })

        logger.info(f"Event creation completed: {len(created_events)} created, {len(failed_events)} failed")

        return {
            "success": True,
            "message": f"Event creation completed: {len(created_events)} created, {len(failed_events)} failed",
            "events_created": len(created_events),
            "events_failed": len(failed_events),
            "created_events": created_events,
            "failed_events": failed_events,
            "team_id": data.team_id,
            "processed_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in create_events: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"Failed to create events: {str(e)}",
            "team_id": data.team_id
        }


async def call_laravel_create_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Laravel API to create a single event in the database.
    """
    try:
        # Laravel backend URL (inside Docker network)
        laravel_url = "http://laravel:8000"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{laravel_url}/api/teams/{event_data['team_id']}/events",
                json=event_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"Successfully created event via Laravel API")
            return {
                "success": True,
                "event": result
            }
        else:
            logger.error(f"Laravel API call failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error calling Laravel API: {e}")
        return {
            "success": False,
            "error": str(e)
        }




if __name__ == "__main__":
    logger.info("Starting Huddle-Up Schedule Agent...")
    app.run()
