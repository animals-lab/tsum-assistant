# Llama Agent

A modern full-stack boilerplate project featuring Next.js frontend with TypeScript and FastAPI backend. This template provides a solid foundation for building scalable web applications with a clean architecture.

## Tech Stack

### Frontend
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- ESLint for code quality
- PNPM for efficient package management

### Backend
- FastAPI (0.109.1+)
- Python 3.12
- Uvicorn ASGI server
- PDM for dependency management

## Prerequisites

- Python 3.12
- PDM (Python dependency manager)
- Node.js 18+
- PNPM (Node.js package manager)

## Setup

Install Python dependencies:
```bash
pdm install
```

## Development

To run both frontend and backend development servers:

```bash
pdm run dev
```

This will:
- Install frontend dependencies automatically (if needed)
- Start frontend server at http://localhost:3000 (Next.js development server)
- Start backend server at http://localhost:8000 (FastAPI with auto-reload)

## Production

To run in production mode:

```bash
pdm run prod
```

## Project Structure

```
llama-agent/
├── .frontend/           # Next.js frontend application
│   ├── app/            # Next.js app directory (App Router)
│   ├── public/         # Static assets
│   ├── tailwind.config.ts  # Tailwind CSS configuration
│   └── package.json    # Frontend dependencies
│
├── api/                # FastAPI backend
│   └── main.py        # Main FastAPI application
│
├── app/                # Python application code
├── run.py             # Development and production server runner
├── pyproject.toml     # Python project configuration
└── pdm.lock           # Python dependency lock file
```

## Features

- Modern frontend with Next.js 14 App Router
- Type-safe development with TypeScript
- Fast and efficient API with FastAPI
- Development and production server configurations
- Tailwind CSS for styling
- Efficient package management with PDM and PNPM
- Hot reloading for both frontend and backend in development

## License

MIT License 