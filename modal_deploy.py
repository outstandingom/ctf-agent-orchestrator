"""
Modal.com Serverless Deployment for CTF AI Orchestrator
Deploys the entire 27-tool FastAPI Command Center to the cloud on Modal serverless infrastructure.
"""

import modal
import os

# Define container image with system tools and Python dependencies
app_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "curl", "libpcap-dev", "libnss3", "libnspr4", "libgbm1")
    .pip_install_from_requirements("requirements.txt")
    .run_commands("pip install playwright && python -m playwright install chromium")
)

app = modal.App(name="ctf-agent-orchestrator", image=app_image)

@app.function(
    secrets=[
        modal.Secret.from_name("ctf-orchestrator-secrets") # Contains GROQ_API_KEY, MCP_API_KEY, etc.
    ],
    timeout=600,
    keep_warm=1
)
@modal.asgi_app()
def fastapi_app():
    import sys
    sys.path.append("/root")
    from server import app as web_app
    return web_app
