# Tsum Shopping Assistant / tsa

GenAI Shopping assistant for TSUM.

## Tech Stack

### Frontend
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS 3.4
- ESLint
- PNPM for efficient package management

### Backend
- FastAPI
- Python 3.12
- Uvicorn ASGI server
- PDM with uv for dependency management
- Llama Index

## Prerequisites

- Python 3.12
- PDM (Python dependency manager)
- Node.js 18+
- PNPM (Node.js package manager)

## Setup & Development

Run both frontend and backend development servers:

```bash
pdm run dev
```

This will:
- Install both backend and frontend dependencies automatically
- Start frontend server at http://localhost:3000 (Next.js development server)
- Start backend server at http://localhost:8000 (FastAPI with auto-reload)

## Production

To run in production mode:

```bash
pdm run prod
```

## Project Structure

```
tsa/
├── frontend/          # Next.js frontend application
│   ├── app/          # Next.js app directory (App Router)
│   ├── components/   # React components
│   ├── lib/          # Utility functions and shared code
│   └── package.json  # Frontend dependencies
│
├── api/              # FastAPI backend
│   ├── routers/     # API route handlers
│   └── server.py    # Main FastAPI application
│
├── tsa/             # Core Python application code
│   ├── chat/        # Chat bot implementation
│   └── catalog/     # Catalog related code
│   └── styleguide/  # Styleguide related code

│   └── run.py       # Development and production server runner
│   └── pyproject.toml   # Python project configuration
│   └── pdm.lock         # Python dependency lock file
```

## Features

- Modern frontend with Next.js 15 and React 19
- Type-safe development with TypeScript
- Fast and efficient API with FastAPI
- LlamaIndex integration for building AI agent workflows
- Development and production server configurations
- Modern UI with Tailwind CSS 3.4
- Efficient package management with PDM and PNPM
- Hot reloading for both frontend and backend in development

## License

MIT License 