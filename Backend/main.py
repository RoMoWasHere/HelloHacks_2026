"""Local FastAPI service that provides the color palette to the Chrome extension."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="HelloHacks Extension API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://.*",
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

PALETTE = [
    {"name": "Green", "hex": "#3aa757"},
    {"name": "Red", "hex": "#e8453c"},
    {"name": "Yellow", "hex": "#f9bb2d"},
    {"name": "Blue", "hex": "#4688f1"},
]


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/colors")
def get_colors():
    return {"colors": PALETTE}
