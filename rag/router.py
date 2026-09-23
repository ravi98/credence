"""Local Semantic Intent Router for Loan Advisory Agent.
Uses an in-memory ephemeral ChromaDB vector collection to match natural language queries
to conversational intents with zero token cost, zero API latency, and complete immunity to rate limits.
"""

import re
from typing import Dict, Any
import chromadb

INTENT_UTTERANCES = [
    # RECOMMENDATION: User seeking loan offers, rates, schemes, or advice on what to pick
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

    # ELIGIBILITY_QUERY: Inquiring about qualification, rules, income limits, documents, or criteria
    ("so can i get homeloan from these banks?", "ELIGIBILITY_QUERY"),
    ("can i get loan from these banks?", "ELIGIBILITY_QUERY"),
    ("do i qualify for these options?", "ELIGIBILITY_QUERY"),
    ("will these banks approve me?", "ELIGIBILITY_QUERY"),
    ("whats the minimum eligiblity?", "ELIGIBILITY_QUERY"),
    ("tell me generic monthly income eligiblity for most of the home loans", "ELIGIBILITY_QUERY"),
    ("do I qualify for a loan with 10k salary", "ELIGIBILITY_QUERY"),
    ("what is the minimum salary required for home loan", "ELIGIBILITY_QUERY"),
    ("what are the eligibility criteria and age limit", "ELIGIBILITY_QUERY"),
    ("what documents are required for application", "ELIGIBILITY_QUERY"),
    ("what paperwork do I need", "ELIGIBILITY_QUERY"),
    ("am I eligible with 700 cibil score", "ELIGIBILITY_QUERY"),
    ("is 10k monthly income enough to get approved", "ELIGIBILITY_QUERY"),
    ("am I qualified for a home loan", "ELIGIBILITY_QUERY"),
    ("can I get approval with 10000 per month", "ELIGIBILITY_QUERY"),
    ("what is the age limit for home loans", "ELIGIBILITY_QUERY"),
    ("salary requirement for personal loan", "ELIGIBILITY_QUERY"),
    ("how much income is needed to get 50 lakhs", "ELIGIBILITY_QUERY"),
    ("who is eligible for this loan", "ELIGIBILITY_QUERY"),

    # COMPARISON: Comparing two institutions or schemes
    ("compare SBI Scholar vs Canara Vidya Turant", "COMPARISON"),
    ("difference between HDFC and ICICI home loan", "COMPARISON"),
    ("which is better SBI or Axis Bank", "COMPARISON"),
    ("compare Kotak Fresh Home Loan versus Federal Bank Housing Loan", "COMPARISON"),
    ("SBI vs HDFC", "COMPARISON"),
    ("compare the two loans", "COMPARISON"),

    # CONCEPT_FAQ: Banking concepts, RBI regulations, tax laws
    ("what is eblr vs mclr", "CONCEPT_FAQ"),
    ("explain prepayment charges under rbi guidelines", "CONCEPT_FAQ"),
    ("what is section 80e tax deduction on education loan", "CONCEPT_FAQ"),
    ("what is cgfsel scheme for education loans", "CONCEPT_FAQ"),
    ("what does foir mean in banking", "CONCEPT_FAQ"),
    ("what is repo rate linked lending rate", "CONCEPT_FAQ"),
    ("what are the tax benefits on home loan", "CONCEPT_FAQ"),

    # EMI_CALCULATOR: Mathematical installment requests
    ("calculate emi for 20 lakhs at 8.5% for 20 years", "EMI_CALCULATOR"),
    ("what is the monthly installment for 50L loan", "EMI_CALCULATOR"),
    ("calculate my emi", "EMI_CALCULATOR"),
    ("what will be my emi for 15 lakhs", "EMI_CALCULATOR"),
    ("calculate emi", "EMI_CALCULATOR"),

    # META_CHAT: Conversational reflections, clarifications, and questions about prior turns
    ("why did u suggest then?", "META_CHAT"),
    ("why did you suggest then", "META_CHAT"),
    ("why did you say that", "META_CHAT"),
    ("why did u say that", "META_CHAT"),
    ("what do you mean by that", "META_CHAT"),
    ("can you clarify your previous response", "META_CHAT"),
    ("why did you recommend them earlier", "META_CHAT"),
    ("explain why you suggested that", "META_CHAT")
]

class SemanticIntentRouter:
    """Zero-cost local intent classifier with lazy initialization and crash-proof fallback."""

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
            print(f"⚠️ ChromaDB ephemeral router disabled ({e}). Running on resilient native semantic matcher.")

    def route(self, query: str) -> str:
        """Determines conversational intent using fast deterministic paths followed by local semantic matching."""
        q = (query or "").lower().strip()

        # 1. Meta-Conversation Fast-Path (Reflections & Clarifications on prior turns)
        meta_keywords = [
            "why did you suggest", "why did u suggest", "why did you say", "why did u say",
            "why did you recommend", "why did u recommend", "what do you mean", "what did you mean",
            "clarify your", "why then", "explain your answer", "explain why you", "you contradicted"
        ]
        if any(k in q for k in meta_keywords):
            return "META_CHAT"

        # 2. Regulatory & FAQ Fast-Path
        if any(k in q for k in ["eblr vs mclr", "mclr vs eblr", "what is eblr", "what is mclr", "rbi guidelines", "section 80e", "cgfsel", "what is foir"]):
            return "CONCEPT_FAQ"

        # 3. Anaphoric Eligibility Checks ("can i get from these banks", "do i qualify for them")
        if any(p in q for p in ["can i get", "am i eligible", "do i qualify", "will i get", "will they approve"]) and any(b in q for b in ["these", "this", "them", "both", "it"]):
            return "ELIGIBILITY_QUERY"

        # 4. EMI Calculator Fast-Path
        if any(k in q for k in ["calculate emi", "what is the emi", "calculate my emi", "monthly installment", "emi for "]):
            return "EMI_CALCULATOR"

        # 5. Comparison Fast-Path
        if any(k in q for k in [" vs ", " vs. ", "versus", "difference between", "better than"]):
            return "COMPARISON"

        # 6. Local ChromaDB Vector Similarity Routing (if available)
        self._ensure_collection()
        if self.collection is not None:
            try:
                results = self.collection.query(query_texts=[q], n_results=1)
                if results and results.get("metadatas") and results["metadatas"][0]:
                    return results["metadatas"][0][0]["intent"]
            except Exception:
                pass

        # 7. Resilient Native Token-Overlap Similarity Matcher (Zero Dependencies)
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

# Singleton instance for fast in-process routing
semantic_router = SemanticIntentRouter()
