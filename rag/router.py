"""Local Semantic Intent Router for Loan Advisory Agent.
Uses fast deterministic pattern matching and local in-memory vector collection
to match natural language queries to conversational intents with zero token cost and zero API latency.
"""

import re
from typing import Dict, Any, Optional
import chromadb

INTENT_UTTERANCES = [
    # RECOMMENDATION / DISCOVERY
    ("can u share the affordable housing options", "RECOMMENDATION"),
    ("help me find lowest interest rate home loan for monthly income of 10k", "RECOMMENDATION"),
    ("recommend best personal loan for salaried employee", "RECOMMENDATION"),
    ("suggest lowest interest car loans", "RECOMMENDATION"),
    ("which bank offers best home loan rate", "RECOMMENDATION"),
    ("find me options for education loan abroad", "RECOMMENDATION"),
    ("give me list of top home loan schemes", "RECOMMENDATION"),
    ("lowest interest rate home loan", "RECOMMENDATION"),
    ("suggest best options for my salary", "RECOMMENDATION"),
    ("recommend home loan for doctor", "RECOMMENDATION"),
    ("which is the cheapest loan available", "RECOMMENDATION"),
    ("what loan can I take", "RECOMMENDATION"),
    ("give me recommendations", "RECOMMENDATION"),
    ("I need a ₹1 crore home loan", "RECOMMENDATION"),
    ("I need a 50 lakh home loan", "RECOMMENDATION"),
    ("I'm salaried, earning ₹1.2 lakh monthly", "RECOMMENDATION"),
    ("I have existing EMIs of ₹15,000", "RECOMMENDATION"),
    ("I need an education loan for MS in the US", "RECOMMENDATION"),
    ("I need an urgent personal loan of 5 lakhs", "RECOMMENDATION"),
    ("I want a car loan for a new Hyundai Creta", "RECOMMENDATION"),

    # ELIGIBILITY_QUERY
    ("so can i get homeloan from these banks?", "ELIGIBILITY_QUERY"),
    ("can i get loan from these banks?", "ELIGIBILITY_QUERY"),
    ("do i qualify for these options?", "ELIGIBILITY_QUERY"),
    ("will these banks approve me?", "ELIGIBILITY_QUERY"),
    ("whats the minimum eligiblity?", "ELIGIBILITY_QUERY"),
    ("tell me generic monthly income eligiblity for most of the home loans", "ELIGIBILITY_QUERY"),
    ("do I qualify for a loan with 10k salary", "ELIGIBILITY_QUERY"),
    ("what is the minimum salary required for home loan", "ELIGIBILITY_QUERY"),
    ("what is the generic minimum salary required for home loans", "ELIGIBILITY_QUERY"),
    ("what are the eligibility criteria and age limit", "ELIGIBILITY_QUERY"),
    ("what documents are required for application", "ELIGIBILITY_QUERY"),
    ("what documents are required for a salaried home loan", "ELIGIBILITY_QUERY"),
    ("what paperwork do I need", "ELIGIBILITY_QUERY"),
    ("am I eligible with 700 cibil score", "ELIGIBILITY_QUERY"),
    ("can I get approval with 10000 per month", "ELIGIBILITY_QUERY"),
    ("salary requirement for personal loan", "ELIGIBILITY_QUERY"),
    ("who is eligible for this loan", "ELIGIBILITY_QUERY"),

    # COMPARISON
    ("compare SBI Scholar vs Canara Vidya Turant", "COMPARISON"),
    ("difference between HDFC and ICICI home loan", "COMPARISON"),
    ("which is better SBI or Axis Bank", "COMPARISON"),
    ("compare Kotak Fresh Home Loan versus Federal Bank Housing Loan", "COMPARISON"),
    ("compare SBI Regular Home Loan vs HDFC Standard Home Loan", "COMPARISON"),
    ("SBI vs HDFC", "COMPARISON"),
    ("compare the two loans", "COMPARISON"),

    # SPECIFIC_PRODUCT_QUERY
    ("explain SBI MaxGain", "SPECIFIC_PRODUCT_QUERY"),
    ("explain SBI MaxGain home loan and how the overdraft facility works", "SPECIFIC_PRODUCT_QUERY"),
    ("what are the foreclosure conditions of HDFC Home Loan", "SPECIFIC_PRODUCT_QUERY"),
    ("tell me about Baroda Advantage Home Loan", "SPECIFIC_PRODUCT_QUERY"),

    # CONCEPT_FAQ
    ("what is eblr vs mclr", "CONCEPT_FAQ"),
    ("what is foir and how do banks calculate it", "CONCEPT_FAQ"),
    ("what does foir mean in banking", "CONCEPT_FAQ"),
    ("explain prepayment charges under rbi guidelines", "CONCEPT_FAQ"),
    ("what is section 80e tax deduction on education loan", "CONCEPT_FAQ"),
    ("what is cgfsel scheme for education loans", "CONCEPT_FAQ"),
    ("what is repo rate linked lending rate", "CONCEPT_FAQ"),

    # EMI_CALCULATOR
    ("calculate emi for 20 lakhs at 8.5% for 20 years", "EMI_CALCULATOR"),
    ("what is the monthly installment for 50L loan", "EMI_CALCULATOR"),
    ("calculate my emi", "EMI_CALCULATOR"),
    ("what will be my emi for 15 lakhs", "EMI_CALCULATOR"),
    ("calculate emi for 50 lakh", "EMI_CALCULATOR"),
    ("calculate emi", "EMI_CALCULATOR"),

    # META_CHAT / CHALLENGE
    ("why wasn't Indian Bank recommended?", "META_CHAT"),
    ("why didn't you suggest Indian Bank?", "META_CHAT"),
    ("why did u suggest then?", "META_CHAT"),
    ("why did you suggest then", "META_CHAT"),
    ("why did you say that", "META_CHAT"),
    ("why did u say that", "META_CHAT"),
    ("what do you mean by that", "META_CHAT"),
    ("can you clarify your previous response", "META_CHAT"),
    ("explain why you suggested that", "META_CHAT")
]

class SemanticIntentRouter:
    def __init__(self):
        self.collection = None
        self._chroma_failed = False

    def _ensure_collection(self):
        if self.collection is not None or self._chroma_failed:
            return
        try:
            client = chromadb.EphemeralClient()
            self.collection = client.get_or_create_collection("intent_routing")
            docs = [item[0] for item in INTENT_UTTERANCES]
            metas = [{"intent": item[1]} for item in INTENT_UTTERANCES]
            ids = [f"utterance_{i}" for i in range(len(INTENT_UTTERANCES))]
            self.collection.add(documents=docs, metadatas=metas, ids=ids)
        except Exception as e:
            self._chroma_failed = True

    def route(self, query: str) -> str:
        q = (query or "").lower().strip()

        # 1. Meta-Conversation & Challenge Fast-Path
        meta_keywords = [
            "why wasn't", "why was not", "why didn't you", "why did not you", "why did u suggest",
            "why did you suggest", "why did you say", "why did u say", "why did you recommend",
            "what do you mean", "clarify your", "explain why you", "you contradicted"
        ]
        if any(k in q for k in meta_keywords):
            return "META_CHAT"

        # 2. Specific Product Query Fast-Path (e.g. "Explain SBI MaxGain", "how does overdraft work")
        if any(k in q for k in ["explain sbi maxgain", "sbi maxgain", "overdraft facility"]):
            return "SPECIFIC_PRODUCT_QUERY"

        # 3. Regulatory & Concept Fast-Path
        if any(k in q for k in ["eblr vs mclr", "mclr vs eblr", "what is eblr", "what is mclr", "rbi guidelines", "section 80e", "cgfsel", "what is foir"]):
            return "CONCEPT_FAQ"

        # 4. Pure EMI Calculation (Only if explicitly asking to calculate, and NOT declaring existing EMIs or salary)
        is_calc_query = any(k in q for k in ["calculate emi", "what is the emi", "calculate my emi", "monthly installment for", "emi for "])
        is_profile_declaration = any(k in q for k in ["i have existing emi", "existing emi of", "other emi", "my income is", "i'm salaried", "im salaried", "earning"])
        if is_calc_query and not is_profile_declaration:
            return "EMI_CALCULATOR"

        # 5. Anaphoric Eligibility Checks or Documentation Queries
        if any(k in q for k in ["what documents", "paperwork", "kyc required", "minimum salary required", "generic minimum salary"]):
            return "ELIGIBILITY_QUERY"
        if any(p in q for p in ["can i get", "am i eligible", "do i qualify", "will i get", "will they approve"]) and any(b in q for b in ["these", "this", "them", "both", "it"]):
            return "ELIGIBILITY_QUERY"

        # 6. Comparison Fast-Path
        if any(k in q for k in [" vs ", " vs. ", "versus", "difference between", "better than"]):
            return "COMPARISON"

        # 7. Clarification Answer / Parameter Declaration Fast-Path
        # Prevents short responses (e.g. "20 Years (240 mo)", "₹50 - ₹75 Lakhs") from being misrouted to EMI calculator or FAQs
        if any(re.search(pat, q) for pat in [
            r"^\s*\d+\s*(?:years?|yrs?|yr|months?|mo)\b",
            r"\b(?:years?|months?)\s*\(\d+\s*mo\)",
            r"^\s*₹?\d+.*(?:cr|crore|lakh|lac|l|k)\b",
            r"^\s*(?:salaried|self-employed|professional)\b",
            r"^\s*(?:lowest\s*total\s*interest|lowest\s*monthly\s*installment|lower\s*emi|fastest\s*sanction|minimal\s*fees)\b",
            r"^\s*looking\s*for.*loan"
        ]):
            return "RECOMMENDATION"

        # 8. Local ChromaDB Vector Similarity
        self._ensure_collection()
        if self.collection is not None:
            try:
                results = self.collection.query(query_texts=[q], n_results=1)
                if results and results.get("metadatas") and results["metadatas"][0]:
                    return results["metadatas"][0][0]["intent"]
            except Exception:
                pass

        # 8. Token-overlap matcher fallback
        q_words = set(q.split())
        best_score = 0.0
        best_intent = "RECOMMENDATION"
        for doc, intent in INTENT_UTTERANCES:
            d_words = set(doc.lower().split())
            union = len(q_words | d_words)
            if union > 0:
                score = len(q_words & d_words) / union
                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_score >= 0.25:
            return best_intent

        return "RECOMMENDATION"

semantic_router = SemanticIntentRouter()
