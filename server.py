import json
import math
import os
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Load environment configuration
load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")
model_name = os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")

from rag.graph import loan_advisor_graph

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "catalog_manifest.json")
try:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        CATALOG_DATA = json.load(f)
        ALL_SCHEMES = CATALOG_DATA.get("schemes", [])
except Exception as e:
    ALL_SCHEMES = []

app = FastAPI(
    title="FinNav AI Loan Advisor API",
    description="LangGraph + ChromaDB Grounded RAG backend for verified Indian retail loans",
    version="1.0.0"
)

# Enable CORS for local Vite dev server & production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserProfileModel(BaseModel):
    employment: Optional[str] = "Salaried"
    cibil_score: Optional[int] = 750
    income: Optional[str] = None
    requested_amount: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None

class ChatRequest(BaseModel):
    chat_id: Optional[str] = Field(default_factory=lambda: f"chat_{uuid.uuid4().hex[:8]}")
    query: str
    user_profile: Optional[UserProfileModel] = None

class ChatResponse(BaseModel):
    chat_id: str
    final_response: str
    intent: str
    candidates: List[Dict[str, Any]] = []

class EMIRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Principal loan amount in Rupees")
    rate: float = Field(..., gt=0, le=50, description="Annual interest rate percentage")
    tenure_years: float = Field(..., gt=0, le=40, description="Tenure in years")

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "FinNav Loan Advisor API",
        "verified_schemes": len(ALL_SCHEMES),
        "institutions": 34,
        "model": model_name,
        "groq_configured": bool(groq_api_key)
    }

@app.get("/api/presets")
async def get_presets():
    return {
        "categories": ["All", "Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan"],
        "sectors": ["All", "Public", "Private", "NBFC", "Co-operative"],
        "employment_types": [
            "Salaried",
            "Self-Employed / Business",
            "Student",
            "Pensioner",
            "Doctor / Professional",
            "Other"
        ],
        "quick_prompts": [
            {
                "title": "Compare Education Loans",
                "prompt": "Compare SBI Scholar Loan vs Canara Vidya Turant",
                "badge": "Comparison"
            },
            {
                "title": "EBLR vs MCLR Benchmark",
                "prompt": "What is EBLR vs MCLR and which is better?",
                "badge": "Regulation"
            },
            {
                "title": "Calculate Loan EMI",
                "prompt": "Calculate EMI for 20 Lakhs at 8.75% for 7 years",
                "badge": "Calculator"
            },
            {
                "title": "Doctor Overdraft Loan",
                "prompt": "Doctor wanting flexible overdraft personal loan",
                "badge": "Advisory"
            },
            {
                "title": "Compare Car Loans",
                "prompt": "Compare HDFC Xpress Car Loan vs SBI New Car Loan",
                "badge": "Comparison"
            }
        ]
    }

@app.get("/api/schemes")
async def list_schemes(
    category: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    results = ALL_SCHEMES

    if category and category.lower() != "all":
        results = [s for s in results if s.get("category", "").lower() == category.lower()]

    if sector and sector.lower() != "all":
        results = [s for s in results if s.get("sector", "").lower() == sector.lower()]

    if search and search.strip():
        q = search.strip().lower()
        results = [
            s for s in results
            if q in s.get("scheme_name", "").lower()
            or q in s.get("institution", "").lower()
            or q in s.get("category", "").lower()
            or q in s.get("compact_key", "").lower()
        ]

    total = len(results)
    paginated = results[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "schemes": paginated
    }

@app.get("/api/schemes/{key}")
async def get_scheme(key: str):
    target = None
    for s in ALL_SCHEMES:
        if s.get("compact_key") == key or s.get("scheme_slug") == key:
            target = s
            break

    if not target:
        raise HTTPException(status_code=404, detail="Scheme not found")

    content_markdown = ""
    file_path = target.get("file_path") or ""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content_markdown = f.read()
        except Exception:
            pass

    return {
        "metadata": target,
        "document": content_markdown
    }

@app.post("/api/calculate/emi")
async def calculate_emi(req: EMIRequest):
    P = req.amount
    annual_rate = req.rate
    years = req.tenure_years
    n = int(years * 12)

    r = (annual_rate / 100) / 12
    if r == 0:
        emi = P / n
    else:
        emi = (P * r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)

    total_payment = emi * n
    total_interest = total_payment - P

    return {
        "principal": round(P, 2),
        "annual_rate": annual_rate,
        "tenure_years": years,
        "tenure_months": n,
        "monthly_emi": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_payment": round(total_payment, 2),
        "interest_ratio_percent": round((total_interest / total_payment) * 100, 1) if total_payment > 0 else 0
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chat_id = request.chat_id or f"chat_{uuid.uuid4().hex[:8]}"

    # Map user profile to the format expected by LangGraph
    user_profile_dict = {}
    if request.user_profile:
        user_profile_dict = {
            "Employment": request.user_profile.employment,
            "CIBIL Score": request.user_profile.cibil_score,
            "Income": request.user_profile.income if request.user_profile.income else None,
            "Requested Amount": request.user_profile.requested_amount if request.user_profile.requested_amount else None,
            "Category Filter": request.user_profile.category if request.user_profile.category and request.user_profile.category != "All" else None,
            "Sector Filter": request.user_profile.sector if request.user_profile.sector and request.user_profile.sector != "All" else None
        }

    graph_input = {
        "chat_id": chat_id,
        "query": request.query.strip(),
        "user_profile": user_profile_dict,
        "api_key": groq_api_key,
        "model_name": model_name
    }

    try:
        # LangGraph invoke with session memory thread persistence
        result_state = loan_advisor_graph.invoke(
            graph_input,
            config={"configurable": {"thread_id": chat_id}}
        )

        final_response = result_state.get("final_response", "")
        detected_intent = result_state.get("intent", "RECOMMENDATION")
        candidates = result_state.get("candidates", [])

        return ChatResponse(
            chat_id=chat_id,
            final_response=final_response,
            intent=detected_intent,
            candidates=candidates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

# Mount static files and handle SPA routes if frontend is built
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse

    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not catch /api endpoints
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
