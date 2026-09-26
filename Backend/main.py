"""Local FastAPI service that the Rental Fraud Detector Chrome extension calls."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="HelloHacks Extension API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://.*",
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

PALETTE = [
    {"name": "Green", "hex": "#3aa757"},
    {"name": "Red", "hex": "#e8453c"},
    {"name": "Yellow", "hex": "#f9bb2d"},
    {"name": "Blue", "hex": "#4688f1"},
]


class Seller(BaseModel):
    name: str = ""
    profile_url: str = ""
    joined: str | None = None


class Listing(BaseModel):
    title: str = ""
    price: float | None = None
    currency: str = "USD"
    description: str = ""
    location: str = ""
    images: list[str] = []
    seller: Seller = Seller()


class AnalyzeRequest(BaseModel):
    source: str
    url: str
    listing: Listing


class Reason(BaseModel):
    code: str
    title: str
    evidence: str


class AnalyzeResponse(BaseModel):
    risk_score: int
    risk_level: str
    reasons: list[Reason]
    model_version: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/colors")
def get_colors():
    return {"colors": PALETTE}


@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Dummy response until the model is wired in
    return AnalyzeResponse(
        risk_score=78,
        risk_level="high",
        reasons=[
            Reason(
                code="OWNER_ABROAD",
                title="Owner claims to be out of the country",
                evidence="Description mentions the owner is away and cannot show the unit.",
            ),
            Reason(
                code="OFF_PLATFORM_PAYMENT",
                title="Asks for deposit through an off-platform payment",
                evidence="Description requests a deposit via Zelle before viewing.",
            ),
            Reason(
                code="PRICE_BELOW_MARKET",
                title="Price is well below the area average",
                evidence=f"Listed at {req.listing.price} {req.listing.currency} in {req.listing.location or 'unknown location'}.",
            ),
        ],
        model_version="dummy-0.1.0",
    )
