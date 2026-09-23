import os
import uuid
import streamlit as st
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Resolve API key & Model securely from environment or Streamlit Cloud Secrets
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        groq_api_key = None

model_name = os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")
if not os.environ.get("MODEL_NAME"):
    try:
        model_name = st.secrets.get("MODEL_NAME", "qwen/qwen3.8-27b")
    except Exception:
        model_name = "qwen/qwen3.8-27b"

from rag.graph import loan_advisor_graph

# Session Chat ID initialization
if "chat_id" not in st.session_state:
    st.session_state.chat_id = f"chat_{uuid.uuid4().hex[:8]}"

# Page configuration
st.set_page_config(
    page_title="FinNav — Indian Loan Advisor AI (LangGraph)",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .intent-badge {
        background-color: #EEF2FF;
        border: 1px solid #C7D2FE;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #4338CA;
        display: inline-block;
        margin-bottom: 10px;
    }
    .disclaimer-box {
        background-color: #F9FAFB;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #374151;
        margin-top: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar: Configuration & Controls
with st.sidebar:
    st.subheader("🎯 Search & Filter Presets")
    category = st.selectbox(
        "Loan Category Filter",
        ["All", "Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan"],
        index=0
    )
    sector = st.selectbox(
        "Banking Sector Filter",
        ["All", "Public", "Private", "NBFC", "Co-operative"],
        index=0
    )

    st.subheader("👤 User Profile Details")
    emp_type = st.selectbox(
        "Employment Type",
        ["Salaried", "Self-Employed / Business", "Student", "Pensioner", "Doctor / Professional", "Other"]
    )
    cibil_score = st.slider("CIBIL / Credit Score", 300, 900, 750)
    monthly_income = st.text_input("Monthly Income / Annual CTC", placeholder="e.g., Rs. 60,000 / month")
    loan_amount = st.text_input("Loan Amount Requested", placeholder="e.g., Rs. 20 Lakhs")

    st.divider()
    st.caption(f"🆔 **Active Session ID**: `{st.session_state.chat_id}`")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ New Chat", use_container_width=True, help="Create a brand new chat session with fresh memory"):
            st.session_state.chat_id = f"chat_{uuid.uuid4().hex[:8]}"
            st.session_state.messages = []
            st.rerun()
    with col_btn2:
        if st.button("🗑️ Clear Screen", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    st.markdown("### 💡 Quick Try Prompts")
    quick_prompts = [
        "Compare SBI Scholar Loan vs Canara Vidya Turant",
        "What is EBLR vs MCLR and which is better?",
        "Calculate EMI for 20 Lakhs at 8.75% for 7 years",
        "Doctor wanting flexible overdraft personal loan",
        "Compare HDFC Xpress Car Loan vs SBI New Car Loan"
    ]
    for p in quick_prompts:
        if st.button(f"👉 {p[:38]}...", help=p):
            st.session_state.selected_prompt = p

# Main Area
st.markdown('<div class="main-header">🏦 FinNav — Indian Loan Advisor AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by LangGraph Agent + ChromaDB Grounded RAG + Qwen Model</div>', unsafe_allow_html=True)

# Metrics Strip
col1, col2, col3, col4 = st.columns(4)
col1.metric("Verified Schemes", "163")
col2.metric("Institutions", "34")
col3.metric("LangGraph Nodes", "Compare, Calc, FAQ, Rec")
col4.metric("Engine Guardrails", "Strict Grounding")

st.markdown("""
<div class="disclaimer-box">
    <strong>🛡️ Anti-Hallucination & Mathematical Precision:</strong> All interest rates, benchmarks, loan quantum limits, and eligibility criteria are retrieved directly from official bank filings. EMI figures are calculated deterministically in Python.
</div>
""", unsafe_allow_html=True)

# Session State for Chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I am **FinNav**, your verified Indian loan advisor powered by **LangGraph**.\n\n"
                "I can help you with:\n"
                "- ⚖️ **Direct Side-by-Side Comparisons** (e.g. *'Compare SBI Scholar vs Canara Vidya Turant'*)\n"
                "- 🔍 **Personalized Recommendations** (e.g. *'Doctor looking for overdraft credit line'*)\n"
                "- 🧮 **Exact EMI Calculations** (e.g. *'Calculate EMI for 15 Lakhs at 8.75% for 7 years'*)\n"
                "- 📚 **Indian Banking Concepts** (e.g. *'What is EBLR vs MCLR?'*, *'Section 80E tax rules'*)\n\n"
                "How can I assist your loan search today?"
            )
        }
    ]

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "intent" in msg and msg["intent"]:
            intent_icons = {
                "COMPARISON": "⚖️ Scheme Comparison",
                "RECOMMENDATION": "🔍 Personalized Recommendation",
                "CONCEPT_FAQ": "📚 Banking Concept & Regulation",
                "ELIGIBILITY_QUERY": "📋 Eligibility & Criteria",
                "META_CHAT": "💬 Clarification",
                "EMI_CALCULATOR": "🧮 Exact EMI Calculation"
            }
            if msg.get("intent") == "RECOMMENDATION" and not msg.get("candidates"):
                badge_text = "⚠️ Eligibility Advisory"
            else:
                badge_text = intent_icons.get(msg["intent"], f"⚡ {msg['intent']}")
            st.markdown(f'<span class="intent-badge">{badge_text}</span>', unsafe_allow_html=True)

        st.markdown(msg["content"])

        if "candidates" in msg and msg["candidates"]:
            with st.expander("🔍 View Retrieved Verified Catalog Data"):
                for c in msg["candidates"]:
                    m = c["metadata"]
                    st.markdown(f"**{m.get('scheme_name')}** ({m.get('institution')}) — Rate: `{m.get('interest_rate_range')}` | [Official Portal]({m.get('source_url')})")

# Prompt Handling
prompt = st.chat_input("Ask about loans, request comparisons, or calculate EMIs...")

if "selected_prompt" in st.session_state and st.session_state.selected_prompt:
    prompt = st.session_state.selected_prompt
    del st.session_state.selected_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    user_profile = {
        "Employment": emp_type,
        "CIBIL Score": cibil_score,
        "Income": monthly_income if monthly_income else None,
        "Requested Amount": loan_amount if loan_amount else None,
        "Category Filter": category if category != "All" else None,
        "Sector Filter": sector if sector != "All" else None
    }

    with st.chat_message("assistant"):
        with st.spinner("Processing through LangGraph workflow (Router → Retrieval → Verification)..."):
            # Execute LangGraph pipeline
            graph_input = {
                "chat_id": st.session_state.chat_id,
                "query": prompt,
                "user_profile": user_profile,
                "api_key": groq_api_key,
                "model_name": model_name
            }

            # Invoke with session checkpointer thread_id
            result_state = loan_advisor_graph.invoke(
                graph_input,
                config={"configurable": {"thread_id": st.session_state.chat_id}}
            )

            detected_intent = result_state.get("intent", "RECOMMENDATION")
            final_text = result_state.get("final_response", "")
            candidates = result_state.get("candidates", [])

            intent_icons = {
                "COMPARISON": "⚖️ Scheme Comparison",
                "RECOMMENDATION": "🔍 Personalized Recommendation",
                "CONCEPT_FAQ": "📚 Banking Concept & Regulation",
                "ELIGIBILITY_QUERY": "📋 Eligibility & Criteria",
                "META_CHAT": "💬 Clarification",
                "EMI_CALCULATOR": "🧮 Exact EMI Calculation"
            }
            if detected_intent == "RECOMMENDATION" and not candidates:
                badge_text = "⚠️ Eligibility Advisory"
            else:
                badge_text = intent_icons.get(detected_intent, f"⚡ {detected_intent}")
            st.markdown(f'<span class="intent-badge">{badge_text}</span>', unsafe_allow_html=True)
            st.markdown(final_text)

            if candidates:
                with st.expander("🔍 Fact Check: Official Sources for this Answer"):
                    for idx, c in enumerate(candidates, 1):
                        m = c["metadata"]
                        st.markdown(f"**{idx}. {m.get('scheme_name')}** — {m.get('institution')} ({m.get('sector')})")
                        st.markdown(f"- **Key**: `{m.get('compact_key', 'N/A')}`")
                        st.markdown(f"- **Rate**: {m.get('interest_rate_range')} | **Benchmark**: {m.get('benchmark')}")
                        st.markdown(f"- **Official Link**: [{m.get('source_url')}]({m.get('source_url')})")

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_text,
        "intent": detected_intent,
        "candidates": candidates
    })
