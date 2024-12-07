# Llama Agent

A boilerplate project featuring Next.js frontend and FastAPI backend.

## Prerequisites

- Python 3.12
- PDM (Python dependency manager)
- Node.js
- PNPM (Node.js package manager)

## Setup

1. Install Python dependencies:
```bash
pdm install
```

2. Install frontend dependencies:
```bash
cd .frontend && pnpm install
```

## Development

To run both frontend and backend development servers:

```bash
pdm run dev
```

This will start:
- Frontend server at http://localhost:3000
- Backend server at http://localhost:8000

## Production

To run in production mode:

```bash
pdm run prod
```

## Project Structure

```
llama-agent/
├── .frontend/       # Next.js frontend
├── api/            # FastAPI application
├── app/            # Python application code
├── run.py          # Development and production server runner
└── pyproject.toml  # Python project configuration
``` 