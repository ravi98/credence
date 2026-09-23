# 🏦 FinNav / Credence — Indian Loan Advisor AI (Grounded RAG)

A 100% free, zero-hallucination conversational loan recommendation engine built with **Streamlit**, **LangGraph**, **ChromaDB**, and **Groq (Qwen)**.

## Key Features
- **163 Verified Schemes**: Comprehensive coverage of Home Loans, Personal Loans, Education Loans, and Vehicle Loans across 34 top Indian banks and NBFCs (SBI, HDFC, ICICI, BoB, PNB, Canara, Axis, etc.).
- **Zero Hallucination Guardrails**: Closed-domain RAG strictly grounded on verified bank documents with official source citations.
- **Local Semantic Intent Router**: Fast in-memory vector intent routing with zero extra API token cost.
- **Declarative Loan Policy Schema**: Enforces Indian banking qualification standards, FOIR ceilings, and income thresholds.
- **Scheme-Pinned Anaphora Resolution**: Accurately resolves follow-up conversational queries ("can i get homeloan from these banks?", "why did u suggest then?").
- **100% Free**: ChromaDB embedded locally, Streamlit UI, and Groq free tier API.

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd loan_data
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

4. **Run the Streamlit App**:
   ```bash
   streamlit run app.py
   ```

## Deploying to Streamlit Community Cloud (Free)

1. Push this repository to **GitHub**.
2. Sign in to [share.streamlit.io](https://share.streamlit.io) using your GitHub account.
3. Click **New app**, select your repository, branch (`main`), and set the main file path to `app.py`.
4. In **Advanced settings** -> **Secrets**, add your Groq API key:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
5. Click **Deploy!**
