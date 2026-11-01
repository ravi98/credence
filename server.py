import os
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Load environment configuration
load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")
model_name = os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")

from rag.graph import loan_advisor_graph

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

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "FinNav Loan Advisor API",
        "verified_schemes": 163,
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

# Mount static files if frontend is built
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

