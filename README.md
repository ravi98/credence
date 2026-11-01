# 🏦 FinNav / Credence — Indian Loan Advisor AI (Grounded RAG)

A 100% free, zero-hallucination conversational loan recommendation engine built with **Vue 3**, **Vite**, **Tailwind CSS**, **FastAPI**, **LangGraph**, **ChromaDB**, and **Groq (Qwen)**.

## Key Features
- **Modern OpenAI-Style UI**: Lean, dark-mode ChatGPT-inspired interface built with Vue 3, Vite, and Tailwind CSS.
- **163 Verified Schemes**: Comprehensive coverage of Home Loans, Personal Loans, Education Loans, and Vehicle Loans across 34 top Indian banks and NBFCs (SBI, HDFC, ICICI, BoB, PNB, Canara, Axis, etc.).
- **Zero Hallucination Guardrails**: Closed-domain RAG strictly grounded on verified bank documents with official source citations.
- **Local Semantic Intent Router**: Fast in-memory vector intent routing with zero extra API token cost.
- **Declarative Loan Policy Schema**: Enforces Indian banking qualification standards, FOIR ceilings, and income thresholds.
- **Scheme-Pinned Anaphora Resolution**: Accurately resolves follow-up conversational queries ("can i get homeloan from these banks?", "why did u suggest then?").
- **100% Free**: ChromaDB embedded locally, Vue 3 SPA, and Groq free tier API.

## Quick Start (Vue 3 + FastAPI)

1. **Set up API Key**:
   Ensure `.env` contains your Groq API key:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

2. **Run the Full App**:
   ```bash
   python server.py
   ```
   Open **[http://localhost:8000](http://localhost:8000)** in your browser. The FastAPI server serves the compiled, lean Vue 3 OpenAI-style frontend directly!

3. **Frontend Development with Hot Reload (Optional)**:
   ```bash
   # Terminal 1: Run Backend API
   python server.py

   # Terminal 2: Run Vue 3 Vite Dev Server
   cd frontend
   npm run dev
   ```
   Open **[http://localhost:5173](http://localhost:5173)** with instant HMR.

## Legacy Streamlit Interface (Optional)
If you still wish to run the legacy Streamlit UI:
```bash
streamlit run app.py
```
