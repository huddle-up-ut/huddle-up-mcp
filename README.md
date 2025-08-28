# Huddle-Up MCP Agents

This repository contains the AI agent infrastructure for the Huddle-Up sports team management application. Each agent runs as an MCP (Model Context Protocol) server in its own Docker container.

## Architecture

- **Team Captain Agent** (Port 8001): Orchestrator agent that exposes high-level tools and delegates to sub-agents
- **Schedule Agent** (Port 8002): Handles schedule parsing, updates, and retrieval
- **Attendance Agent** (Port 8003): Manages attendance recording and analysis

## Communication Flow

```
Laravel Backend → Team Captain Agent → Sub-agents (Schedule, Attendance)
```

- Laravel communicates with Team Captain Agent via HTTP
- Team Captain Agent communicates with sub-agents via MCP protocol over Docker network
- All agents share the `huddle-up-net` Docker network

## Quick Start

### Prerequisites
- Docker and Docker Compose
- The `huddle-up-net` network must exist (created by main infrastructure)

### Run All Agents
```bash
docker compose up -d --build
```

### Test Individual Agents
```bash
# Team Captain Agent
curl http://localhost:8001/health

# Schedule Agent  
curl http://localhost:8002/health

# Attendance Agent
curl http://localhost:8003/health
```

## Development

Each agent is a FastAPI application using FastMCP for MCP protocol handling. The agents are currently stubbed with placeholder implementations.

### Adding New Agents
1. Create a new directory in the root
2. Add `main.py`, `Dockerfile`, and `requirements.txt`
3. Add the service to `docker-compose.yml`
4. Update the Team Captain Agent to orchestrate the new agent

## Ports
- Team Captain Agent: 8001
- Schedule Agent: 8002  
- Attendance Agent: 8003

## Health Checks
All agents include health check endpoints at `/health` for Docker health monitoring. 