import asyncio
import os
from asyncio.subprocess import Process
from pathlib import Path
import sys
from subprocess import CalledProcessError, run
from shutil import which

FRONTEND_DIR = ".frontend"

def _get_node_package_manager() -> str:
    """
    Check for available package managers and return the preferred one.
    Returns 'pnpm' if installed, falls back to 'npm'.
    Raises SystemError if neither is installed.
    """
    pnpm_cmds = ["pnpm", "pnpm.cmd"]
    npm_cmds = ["npm", "npm.cmd"]

    for cmd in pnpm_cmds:
        cmd_path = which(cmd)
        if cmd_path is not None:
            return cmd_path

    for cmd in npm_cmds:
        cmd_path = which(cmd)
        if cmd_path is not None:
            return cmd_path

    raise SystemError(
        "Neither pnpm nor npm is installed. Please install Node.js and a package manager first."
    )

def _install_frontend_dependencies():
    """Install frontend dependencies using the available package manager"""
    package_manager = _get_node_package_manager()
    print(f"\nInstalling frontend dependencies using {Path(package_manager).name}...")
    run([package_manager, "install"], cwd=FRONTEND_DIR, check=True)

async def start_frontend_dev():
    """Start the Next.js development server"""
    _install_frontend_dependencies()
    
    process = await asyncio.create_subprocess_shell(
        f"cd {FRONTEND_DIR} && pnpm dev",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True
    )
    return process

async def start_backend_dev():
    """Start the FastAPI development server"""
    process = await asyncio.create_subprocess_shell(
        "uvicorn api.main:app --reload --port 8000",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True
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
    process = await asyncio.create_subprocess_shell(
        "uvicorn api.main:app --host 0.0.0.0 --port 8000",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True
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