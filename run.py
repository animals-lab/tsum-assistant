import asyncio
import os
from asyncio.subprocess import Process
from pathlib import Path
import sys
from subprocess import CalledProcessError, run
from shutil import which, copyfile

FRONTEND_DIR = "frontend"

def _setup_frontend_config():
    """Setup frontend configuration files"""
    # Create root .env if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write("# Frontend settings\n")
            f.write("NEXT_PUBLIC_APP_URL=http://localhost:3000\n\n")
            f.write("# Backend settings\n")
            f.write("OPENAI_API_KEY=\n")

def _check_pnpm() -> str:
    """
    Check if pnpm is installed.
    Returns pnpm path if installed, raises SystemError if not.
    """
    pnpm_cmds = ["pnpm", "pnpm.cmd"]

    for cmd in pnpm_cmds:
        cmd_path = which(cmd)
        if cmd_path is not None:
            return cmd_path

    raise SystemError(
        "pnpm is not installed. Please install pnpm first: https://pnpm.io/installation"
    )

def _install_frontend_dependencies():
    """Install frontend dependencies using pnpm"""
    _setup_frontend_config()
    pnpm = _check_pnpm()
    print(f"\nInstalling frontend dependencies using pnpm...")
    
    # Set environment variables from root .env
    env = os.environ.copy()
    if Path(".env").exists():
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key] = value
    
    run([pnpm, "install"], cwd=FRONTEND_DIR, check=True, env=env)

def _install_backend_dependencies():
    """Install backend dependencies using PDM"""
    print("\nChecking backend dependencies with PDM...")
    try:
        run(["pdm", "install"], check=True)
    except CalledProcessError as e:
        print(f"Error installing backend dependencies: {str(e)}")
        sys.exit(1)
    except FileNotFoundError:
        print("PDM not found. Please install PDM first.")
        sys.exit(1)

async def start_frontend_dev():
    """Start the Next.js development server"""
    _install_frontend_dependencies()
    
    # Set environment variables from root .env
    env = os.environ.copy()
    if Path(".env").exists():
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key] = value
    
    process = await asyncio.create_subprocess_shell(
        f"cd {FRONTEND_DIR} && pnpm dev",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True,
        env=env
    )
    return process

async def start_backend_dev():
    """Start the FastAPI development server with reload enabled"""
    _install_backend_dependencies()
    
    # Set environment variables from root .env
    env = os.environ.copy()
    if Path(".env").exists():
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key] = value
    
    process = await asyncio.create_subprocess_shell(
        "pdm run uvicorn tsa.api.server:app --reload --host 0.0.0.0 --port 8000",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True,
        env=env
    )
    return process

async def start_development_servers():
    """Start both frontend and backend development servers"""
    try:
        frontend = await start_frontend_dev()
        backend = await start_backend_dev()
        
        await asyncio.gather(
            frontend.wait(),
            backend.wait()
        )
    except CalledProcessError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        if 'frontend' in locals():
            frontend.terminate()
            await frontend.wait()
        if 'backend' in locals():
            backend.terminate()
            await backend.wait()

async def start_production_server():
    """Start the production server"""
    _install_backend_dependencies()
    
    # Set environment variables from root .env
    env = os.environ.copy()
    if Path(".env").exists():
        with open(".env") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key] = value
    
    process = await asyncio.create_subprocess_shell(
        "pdm run uvicorn tsa.api.server:app --host 0.0.0.0 --port 8000",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True,
        env=env
    )
    try:
        await process.wait()
    except KeyboardInterrupt:
        process.terminate()
        await process.wait()

def dev():
    """Run development servers"""
    asyncio.run(start_development_servers())

def prod():
    """Run production server"""
    asyncio.run(start_production_server())

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["dev", "prod"]:
        print("Usage: python run.py [dev|prod]")
        sys.exit(1)
    
    globals()[sys.argv[1]]() 