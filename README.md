---
title: Credence Indian Loan Advisor AI
emoji: 🏦
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
pinned: false
---

# 🏦 FinNav / Credence — Indian Loan Advisor AI (Grounded RAG)

A 100% free, zero-hallucination conversational loan recommendation engine built with **Gradio**, **LangGraph**, **ChromaDB**, and the **Qwen / Groq** model.

## Features
- **163 Verified Schemes**: Covers Home Loans, Personal Loans, Education Loans, and Vehicle Loans across 34 top Indian banks and NBFCs (SBI, HDFC, ICICI, BoB, PNB, Canara, Axis, etc.).
- **Zero Hallucination Guardrails**: Closed-domain RAG strictly grounded on verified bank documents with official source citations.
- **Local Semantic Intent Router**: Fast in-memory vector intent routing with zero extra API token cost.
- **Declarative Loan Policy Schema**: Enforces Indian banking qualification standards, FOIR ceilings, and income thresholds.
- **100% Free**: ChromaDB embedded locally, Gradio UI, and Groq free tier API.

## Local Execution
- **Run Gradio App**: `python app.py`
- **Run Streamlit App**: `streamlit run streamlit_app.py`
