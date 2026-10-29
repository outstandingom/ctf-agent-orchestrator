import sys
import os
import traceback

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from server import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI(title="CTF Orchestrator Diagnostic")
    err_text = str(e)
    tb_text = traceback.format_exc()

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def diagnostic_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Cold start import failed on Vercel",
                "error": err_text,
                "traceback": tb_text.splitlines()
            }
        )
