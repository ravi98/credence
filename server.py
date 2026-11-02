import json
import math
import os
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Load environment configuration
load_dotenv()

groq_api_key = os.environ.get("GROQ_API_KEY")
model_name = os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")

from rag.graph import loan_advisor_graph
from sqlalchemy.orm import Session
from database import get_db
import auth
from auth_deps import get_current_user, get_optional_current_user, require_roles
from models.user import User, UserRole
from routers.enquiries import router as enquiries_router
from routers.sales import router as sales_router

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "catalog_manifest.json")
try:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        CATALOG_DATA = json.load(f)
        ALL_SCHEMES = CATALOG_DATA.get("schemes", [])
except Exception as e:
    ALL_SCHEMES = []

app = FastAPI(
    title="Credence AI Loan Advisor API",
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

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class AuthUser(BaseModel):
    id: str
    email: str
    name: str
    role: str = "CUSTOMER"
    auth_provider: str
    avatar_url: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: AuthUser

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Credence Loan Advisor API",
        "verified_schemes": len(ALL_SCHEMES),
        "institutions": 34,
        "model": model_name,
        "groq_configured": bool(groq_api_key)
    }

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email format.")

    existing = auth.get_user_by_email(email, db=db)
    if existing:
        # If user registered with Google previously without a password, link the password
        if existing.google_id and not existing.password_hash:
            pwd_hash = auth.hash_password(req.password)
            existing.password_hash = pwd_hash
            existing.auth_provider = "both"
            db.commit()
            db.refresh(existing)
            token = auth.create_access_token(existing.id, existing.email, existing.name, role=existing.role)
            return AuthResponse(
                token=token,
                user=AuthUser(
                    id=existing.id,
                    email=existing.email,
                    name=existing.name,
                    role=str(existing.role.value if hasattr(existing.role, "value") else existing.role),
                    auth_provider=existing.auth_provider,
                    avatar_url=existing.avatar_url
                )
            )
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = auth.create_user(
        email=email,
        name=req.name.strip(),
        password=req.password,
        role=UserRole.CUSTOMER,
        auth_provider="email",
        db=db
    )
    token = auth.create_access_token(user.id, user.email, user.name, role=user.role)
    return AuthResponse(
        token=token,
        user=AuthUser(
            id=user.id,
            email=user.email,
            name=user.name,
            role=str(user.role.value if hasattr(user.role, "value") else user.role),
            auth_provider=user.auth_provider,
            avatar_url=user.avatar_url
        )
    )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = auth.get_user_by_email(email, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.password_hash:
        raise HTTPException(
            status_code=400, 
            detail="This account was registered using Google. Please sign in with 'Continue with Google'."
        )

    if not auth.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = auth.create_access_token(user.id, user.email, user.name, role=user.role)
    return AuthResponse(
        token=token,
        user=AuthUser(
            id=user.id,
            email=user.email,
            name=user.name,
            role=str(user.role.value if hasattr(user.role, "value") else user.role),
            auth_provider=user.auth_provider,
            avatar_url=user.avatar_url
        )
    )

@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    if not req.credential:
        raise HTTPException(status_code=400, detail="Missing Google credential token.")

    try:
        google_profile = auth.verify_google_credential(req.credential)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    email = google_profile["email"].strip().lower()
    google_id = google_profile.get("google_id")

    # Step 1: Check if already recognized by google_id
    existing = None
    if google_id:
        existing = auth.get_user_by_google_id(google_id, db=db)

    # Step 2: If not found by google_id, check if user exists by verified email
    if not existing:
        existing = auth.get_user_by_email(email, db=db)
        if existing and google_id:
            # Seamlessly link this Google identity to the existing user record
            existing = auth.link_google_account(
                user_id=existing.id,
                google_id=google_id,
                avatar_url=google_profile.get("avatar_url"),
                db=db
            )

    # Step 3: If user exists (previously linked or freshly linked to existing email)
    if existing:
        token = auth.create_access_token(existing.id, existing.email, existing.name, role=existing.role)
        return AuthResponse(
            token=token,
            user=AuthUser(
                id=existing.id,
                email=existing.email,
                name=existing.name,
                role=str(existing.role.value if hasattr(existing.role, "value") else existing.role),
                auth_provider=existing.auth_provider,
                avatar_url=existing.avatar_url or google_profile.get("avatar_url")
            )
        )

    # Step 4: Completely new user registering via Google
    new_user = auth.create_user(
        email=email,
        name=google_profile.get("name", "Google User"),
        password=None,
        role=UserRole.CUSTOMER,
        auth_provider="google",
        google_id=google_id,
        avatar_url=google_profile.get("avatar_url"),
        db=db
    )
    token = auth.create_access_token(new_user.id, new_user.email, new_user.name, role=new_user.role)
    return AuthResponse(
        token=token,
        user=AuthUser(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            role=str(new_user.role.value if hasattr(new_user.role, "value") else new_user.role),
            auth_provider=new_user.auth_provider,
            avatar_url=new_user.avatar_url
        )
    )

@app.get("/api/auth/me", response_model=AuthUser)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return AuthUser(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role),
        auth_provider=current_user.auth_provider,
        avatar_url=current_user.avatar_url
    )

@app.get("/api/auth/google/config")
async def get_google_auth_config():
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    return {
        "google_client_id": client_id
    }

# Register Enquiries & Sales CRM Routers
app.include_router(enquiries_router, prefix="/api/enquiries", tags=["enquiries"])
app.include_router(sales_router, prefix="/api/sales", tags=["sales"])

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
