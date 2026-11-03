import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class CandidateTraceItem(BaseModel):
    institution: str
    scheme_name: str
    status: str # "SHORTLISTED", "EXCLUDED", "LOWER_RANKED"
    reason: str
    effective_rate: Optional[float] = None
    estimated_emi: Optional[float] = None

class DecisionTrace(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:10]}")
    chat_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    profile_version: int = 1
    parameters_used: Dict[str, Any] = Field(default_factory=dict)
    candidates_examined_count: int = 0
    shortlisted: List[CandidateTraceItem] = Field(default_factory=list)
    excluded_or_lower_ranked: List[CandidateTraceItem] = Field(default_factory=list)
    ranking_factors: List[str] = Field(default_factory=list)

# In-memory thread decision trace store (persisted alongside LangGraph checkpoint)
_TRACE_STORE: Dict[str, DecisionTrace] = {}

def record_decision_trace(
    chat_id: str,
    profile_summary: Dict[str, Any],
    all_examined: List[Dict[str, Any]],
    shortlisted: List[Dict[str, Any]],
    priorities: List[str]
) -> DecisionTrace:
    trace = DecisionTrace(
        chat_id=chat_id,
        profile_version=profile_summary.get("version", 1),
        parameters_used=profile_summary,
        candidates_examined_count=len(all_examined),
        ranking_factors=priorities
    )

    shortlisted_slugs = {c.get("metadata", {}).get("scheme_slug") for c in shortlisted}

    for c in shortlisted:
        m = c.get("metadata", {})
        rd = c.get("ranking_details", {})
        trace.shortlisted.append(CandidateTraceItem(
            institution=m.get("institution", "Bank"),
            scheme_name=m.get("scheme_name", "Scheme"),
            status="SHORTLISTED",
            reason=f"Top match based on {rd.get('badge', 'favorable terms')} with effective rate {rd.get('effective_rate')}% and estimated EMI ₹{rd.get('estimated_monthly_emi'):,}.",
            effective_rate=rd.get("effective_rate"),
            estimated_emi=rd.get("estimated_monthly_emi")
        ))

    for c in all_examined:
        m = c.get("metadata", {})
        slug = m.get("scheme_slug")
        if slug not in shortlisted_slugs:
            trace.excluded_or_lower_ranked.append(CandidateTraceItem(
                institution=m.get("institution", "Bank"),
                scheme_name=m.get("scheme_name", "Scheme"),
                status="LOWER_RANKED",
                reason=f"Ranked lower due to interest rate ({m.get('interest_rate_range')}) or higher cumulative borrowing cost."
            ))

    _TRACE_STORE[chat_id] = trace
    return trace

def get_latest_trace(chat_id: str) -> Optional[DecisionTrace]:
    return _TRACE_STORE.get(chat_id)

