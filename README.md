---
title: FinNav Indian Loan Advisor AI
emoji: 🏦
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.35.0
app_file: app.py
pinned: false
---

# 🏦 FinNav — Indian Loan Advisor AI (Grounded RAG)

A 100% free, zero-hallucination conversational loan recommendation engine built with **Streamlit**, **ChromaDB**, and **Google Gemini 1.5 Flash**.

## Features
- **163 Verified Schemes**: Covers Home Loans, Personal Loans, Education Loans, and Vehicle Loans across 34 top Indian banks and NBFCs (SBI, HDFC, ICICI, BoB, PNB, Canara, Axis, etc.).
- **Zero Hallucination Guardrails**: Closed-domain RAG strictly grounded on verified bank documents with official source citations.
- **Hybrid Search**: Natural language semantic matching with hard metadata filters (Category, Sector, Tenure, CIBIL, Income).
- **100% Free**: ChromaDB embedded locally, Streamlit UI, and Gemini 1.5 Flash free tier API.

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/loan_data.git
   cd loan_data
   ```

2. **Set up virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Build ChromaDB Index**:
   ```bash
   python rag/indexer.py
   ```

4. **Run Streamlit App**:
   ```bash
   streamlit run app.py
   ```

## Deploying to Hugging Face Spaces for Free

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space).
2. Select **Streamlit** as the SDK.
3. Push this repository (including `app.py`, `requirements.txt`, `rag/`, `catalog_manifest.json`, and loan data folders).
4. Hugging Face Spaces will automatically run `rag/indexer.py` on first launch or load `./chroma_db`.
