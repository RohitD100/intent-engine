"""Application entry point – builds the FastAPI app and wires the router.
The CLI entry point is still kept in the top‑level `app.py` for backward compatibility.
"""

from fastapi import FastAPI
from .api.router import router

app = FastAPI(title="Intent Engine")
app.include_router(router)
