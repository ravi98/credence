import os
import json
import chromadb
from chromadb.config import Settings

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

SYSTEM_PROMPT = """You are an expert, honest, and highly accurate Indian Bank Loan Advisor.
Your objective is to provide personalized, transparent, and strictly grounded loan recommendations to the user based ONLY on the verified loan catalog data provided below.

CRITICAL ANTI-HALLUCINATION & INTEGRITY RULES:
1. STRICT GROUNDING: You must ONLY recommend and discuss schemes present in the provided "Retrieved Verified Loan Schemes". Do NOT invent, assume, or extrapolate any schemes, interest rates, or eligibility criteria.
2. ACCURATE NUMBERS: Always quote the exact Interest Rate Range, Benchmark, and Maximum Tenure as provided in the scheme metadata. Never fabricate EMI formulas or false discount guarantees.
3. CLEAR ELIGIBILITY WARNINGS: If the user's declared profile (e.g., CIBIL score, income, employment type, or requested amount) seems borderline or doesn't meet the scheme's requirements, explicitly state the disqualifier or requirement under "Important Caveats".
4. SOURCE CITATION: For every scheme you recommend, you MUST include the official bank verification link provided in its metadata.
5. STRUCTURED RESPONSE FORMAT:
   - **Recommendation Summary**: Brief, encouraging 1-2 sentence executive verdict.
   - **Top Matching Schemes**: For each matched scheme:
     • **Scheme Name & Bank** (Sector)
     • **Why this fits your profile**
     • **Verified Interest Rate & Benchmark**
     • **Max Tenure & Loan Quantum**
     • **Processing Fees & Other Charges**
     • **Key Eligibility Highlights**
     • **Official Bank Portal Link**: [Official Site](URL)
   - **Important Caveats & Tips**: Essential advice on CIBIL, documentation, or margin money.
"""

class LoanRecommendationEngine:
    def __init__(self, chroma_path=CHROMA_PATH):
        self.chroma_path = chroma_path
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._client = chromadb.PersistentClient(path=self.chroma_path)
            try:
                self._collection = self._client.get_collection(name="loan_schemes")
            except Exception as e:
                print("ChromaDB collection 'loan_schemes' not found. Automatically building index from catalog...")
                from rag.indexer import build_index
                build_index()
                self._collection = self._client.get_collection(name="loan_schemes")
        return self._collection

    def retrieve(self, query: str, category: str = None, sector: str = None, max_tenure: int = None, section_type: str = None, loan_amount_lakhs: float = None, n_results: int = 4):
        """Retrieve relevant schemes using hybrid metadata filtering and semantic vector search."""
        filter_conditions = []

        if category and category.strip() and category != "All":
            filter_conditions.append({"category": {"$eq": category.strip()}})

        if sector and sector.strip() and sector != "All":
            filter_conditions.append({"sector": {"$eq": sector.strip()}})

        if max_tenure and max_tenure > 0:
            filter_conditions.append({"max_tenure_years": {"$gte": int(max_tenure)}})

        if section_type and section_type.strip():
            filter_conditions.append({"section_type": {"$eq": section_type.strip()}})

        if loan_amount_lakhs is not None and loan_amount_lakhs > 0:
            filter_conditions.append({"min_amount_lakhs": {"$lte": float(loan_amount_lakhs)}})
            filter_conditions.append({"max_amount_lakhs": {"$gte": float(loan_amount_lakhs)}})

        where_clause = None
        if len(filter_conditions) == 1:
            where_clause = filter_conditions[0]
        elif len(filter_conditions) > 1:
            where_clause = {"$and": filter_conditions}

        query_args = {
            "query_texts": [query],
            "n_results": n_results
        }
        if where_clause:
            query_args["where"] = where_clause

        try:
            results = self.collection.query(**query_args)
        except Exception as e:
            # Fallback if where filter is too restrictive or empty
            print(f"Retrieval error with filter {where_clause}: {e}. Falling back to unconstrained search.")
            results = self.collection.query(query_texts=[query], n_results=n_results)

        candidates = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                candidates.append({
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "document": results["documents"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results and results["distances"] else None
                })
        return candidates

    def generate_recommendation(self, user_query: str, user_profile: dict, candidates: list, api_key: str = None):
        """Generate grounded, anti-hallucination recommendation using Gemini or deterministic fallback."""
        if not candidates:
            return (
                "⚠️ **No Matching Schemes Found**\n\n"
                "We could not find any verified schemes matching your exact filter criteria in our catalog. "
                "Try relaxing your category or tenure filters to discover alternative options."
            )

        # Build clean grounded context
        context_blocks = []
        for idx, c in enumerate(candidates, 1):
            m = c["metadata"]
            block = (
                f"### Scheme #{idx}: {m.get('scheme_name')} - {m.get('institution')} ({m.get('sector')})\n"
                f"- Category: {m.get('category')}\n"
                f"- Verified Interest Rate: {m.get('interest_rate_range')}\n"
                f"- Benchmark: {m.get('benchmark')}\n"
                f"- Maximum Tenure: {m.get('max_tenure_years')} years\n"
                f"- Maximum Loan Quantum: {m.get('max_loan_amount')}\n"
                f"- Processing Fee: {m.get('processing_fee')}\n"
                f"- Target Borrowers: {m.get('target_borrowers')}\n"
                f"- Official Verification URL: {m.get('source_url')}\n\n"
                f"Scheme Document Details:\n{c['document'][:1800]}\n"
            )
            context_blocks.append(block)

        retrieved_context = "\n---\n".join(context_blocks)

        profile_str = ", ".join([f"{k}: {v}" for k, v in user_profile.items() if v])

        # If Gemini API Key is available, use Google GenAI SDK
        if api_key and api_key.strip():
            try:
                from google import genai
                client = genai.Client(api_key=api_key.strip())

                prompt = (
                    f"User Declared Profile: {profile_str or 'Not explicitly specified'}\n"
                    f"User Query / Requirement: {user_query}\n\n"
                    f"=== RETRIEVED VERIFIED LOAN SCHEMES (GROUND TRUTH) ===\n"
                    f"{retrieved_context}\n"
                    f"=======================================================\n\n"
                    f"Provide your professional recommendation strictly grounded in the verified schemes above. "
                    f"Follow all anti-hallucination rules and cite the official links for each scheme."
                )

                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={
                        "system_instruction": SYSTEM_PROMPT,
                        "temperature": 0.2,  # Low temperature for strict factual consistency
                    }
                )
                return response.text
            except Exception as e:
                # In case of API quota or key error, append notice and show deterministic view
                return (
                    f"⚠️ *Gemini API call returned an error ({e}). Displaying direct verified catalog results below:*\n\n"
                    + self._build_deterministic_response(user_query, user_profile, candidates)
                )

        # Fallback when no API Key is provided yet: Deterministic Structured Output
        return self._build_deterministic_response(user_query, user_profile, candidates)

    def _build_deterministic_response(self, user_query: str, user_profile: dict, candidates: list):
        """Zero-hallucination deterministic presentation of retrieved schemes when LLM API key is not provided."""
        lines = [
            f"### Verified Matching Schemes for Your Request\n",
            f"*(Displaying direct factual data from official catalog)*\n"
        ]
        for idx, c in enumerate(candidates, 1):
            m = c["metadata"]
            lines.append(f"#### {idx}. {m.get('scheme_name')} — **{m.get('institution')}**")
            lines.append(f"- **Category**: {m.get('category')} | **Sector**: {m.get('sector')}")
            lines.append(f"- **Verified Interest Rate**: **{m.get('interest_rate_range')}** ({m.get('benchmark')})")
            lines.append(f"- **Max Tenure**: {m.get('max_tenure_years')} years")
            lines.append(f"- **Max Loan Amount**: {m.get('max_loan_amount')}")
            lines.append(f"- **Processing Fee**: {m.get('processing_fee')}")
            lines.append(f"- **Target Borrowers**: {m.get('target_borrowers')}")
            lines.append(f"- 🔗 **Official Portal**: [{m.get('institution')} Official Site]({m.get('source_url')})\n")

        lines.append("\n> [!TIP]\n> Paste a free **Google Gemini API Key** in the sidebar to get conversational personalized advice, EMI breakdowns, and profile match comparisons!")
        return "\n".join(lines)
