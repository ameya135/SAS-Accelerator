# Graph Approach Backend

Flask-based REST API backend for the graph-based SAS to PySpark migration tool.

## Overview

This backend provides API endpoints that integrate with the graph_approach core modules:
- **GraphBuilder**: Builds dependency graphs from SAS code
- **ChunkOptimizer**: Generates optimal chunks for migration
- **GraphMigrator**: Orchestrates the complete migration process
- **GraphExporter**: Exports graphs in various formats (React Flow, D3, JSON)

## API Endpoints

### Health Check
```
GET /api/health
```
Returns server health status and module availability.

### Graph Analysis
```
POST /api/graph/analyze
```
Analyzes a SAS file and returns:
- Dependency graph (in React Flow, D3, or JSON format)
- Optimized chunks with token counts
- Summary statistics

**Request**: multipart/form-data
- `file`: SAS file
- `format`: Output format (react-flow, d3, json)

### Migration Session Management

#### Initialize Session
```
POST /api/graph-migrate/initialize
```
Creates a new migration session.

**Request JSON**:
```json
{
  "model": "gpt-4",
  "use_rag": true
}
```

#### Upload Files
```
POST /api/graph-migrate/upload
```
Uploads SAS files to a session.

**Request**: multipart/form-data
- `session_id`: Session ID
- `files[]`: SAS files

#### Start Migration
```
POST /api/graph-migrate/start
```
Starts the graph-based migration process.

**Request JSON**:
```json
{
  "session_id": "uuid"
}
```

#### Download Results
```
GET /api/graph-migrate/download/<session_id>/<filename>
GET /api/graph-migrate/download-all/<session_id>
```

## Running the Backend

### Prerequisites

1. Python 3.9+
2. Azure OpenAI credentials (for migration functionality)

### Setup

```bash
# From repo root
python3 -m pip install -r requirements.txt

# Move into backend directory
cd backend

# Set environment variables, or copy .env.example to .env in the repo root
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export SAS_ACCELERATOR_API_KEY="your-backend-api-key"
export SAS_ACCELERATOR_DEV_MODE=false
export SAS_ACCELERATOR_CORS_ORIGINS="http://localhost:3001"

# Run the backend
./run.sh
# or
python3 app.py
```

The backend runs on port **5002** by default.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Required |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | Required |
| `SAS_ACCELERATOR_API_KEY` | API key for authenticating backend requests | Required |
| `SAS_ACCELERATOR_DEV_MODE` | Enable development-mode behavior | false |
| `SAS_ACCELERATOR_CORS_ORIGINS` | Comma-separated allowed frontend origins | http://localhost:3001 |
| `DEFAULT_MODEL` | Default LLM model | gpt-4 |
| `GRAPH_BACKEND_PORT` | Server port | 5002 |

## Integration with Frontend

The frontend (`frontend/`) is configured to proxy API requests to this backend on port 5002.

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:5002',
    changeOrigin: true,
  },
}
```

## API Response Format

All endpoints return JSON responses with the following structure:

**Success**:
```json
{
  "success": true,
  "data": {...}
}
```

**Error**:
```json
{
  "error": "Error message"
}
```

## Architecture

```
graph_approach/
├── backend/
│   ├── app.py           # Flask application
│   ├── requirements.txt # Backend dependencies
│   ├── run.sh          # Run script
│   └── README.md       # This file
├── core/
│   ├── dependency_graph.py
│   ├── graph_builder.py
│   ├── chunk_optimizer.py
│   └── schema_tracker.py
├── migration/
│   ├── graph_migrator.py
│   ├── context_enricher.py
│   └── code_reconciler.py
├── api/
│   ├── graph_exporter.py
│   └── realtime_migrator.py
└── frontend/
    └── ...
```

## Session Management

- Sessions are stored in memory with automatic cleanup after 24 hours
- Each session has its own temporary directory for file storage
- Sessions can be manually cleaned up via the DELETE endpoint
