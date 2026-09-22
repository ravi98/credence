import os
import json
import re
import chromadb
from chromadb.config import Settings

MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog_manifest.json")
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

SECTION_TYPE_MAP = {
    "overview": "summary",
    "interest rates": "rates",
    "rates": "rates",
    "eligibility": "eligibility",
    "quantum": "quantum",
    "tenure": "quantum",
    "fees": "fees",
    "charges": "fees",
    "documents": "documents",
    "special features": "features",
    "features": "features"
}

def parse_scheme_sections(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter
    fm = {}
    fm_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        for line in fm_match.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip("\"'")

    # Split markdown by H2 headers
    sections = re.split(r"\n##\s+", content)
    parsed_sections = {}

    for s in sections[1:]:
        lines = s.split("\n", 1)
        title = lines[0].strip().lower()
        body = lines[1].strip() if len(lines) > 1 else ""

        # Map to standard section_type
        mapped_type = "general"
        for keyword, stype in SECTION_TYPE_MAP.items():
            if keyword in title:
                mapped_type = stype
                break

        if mapped_type in parsed_sections:
            parsed_sections[mapped_type] += "\n" + body
        else:
            parsed_sections[mapped_type] = body

    return fm, parsed_sections

def build_index():
    print(f"Loading manifest from: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)["schemes"]

    print(f"Initializing persistent ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection_name = "loan_schemes"
    try:
        client.delete_collection(name=collection_name)
        print(f"Deleted existing '{collection_name}' collection for fresh hierarchical indexing.")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Hierarchical Section-Aware Loan Catalog Index"}
    )

    documents = []
    metadatas = []
    ids = []

    print(f"Parsing and creating hierarchical chunks for {len(manifest)} loan schemes...")

    for scheme in manifest:
        file_path = scheme["file_path"]
        if not os.path.exists(file_path):
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), scheme["relative_path"])

        fm, sections = parse_scheme_sections(file_path)

        # Parse tenure to integer
        try:
            tenure_int = int(re.search(r"\d+", str(scheme.get("max_tenure_years", "0"))).group())
        except Exception:
            tenure_int = 0

        # Construct compact composite key
        rate = scheme.get("interest_rate_range", "")
        m = re.search(r"(\d+(\.\d+)?)%", rate)
        min_rate = f"{m.group(1)}%" if m else "N/A"
        sector = scheme.get("sector", "").lower()
        tenure_str = f"{scheme.get('max_tenure_years', '0')}y"
        cat_str = scheme.get("category", "").lower().replace(" ", "-")
        inst_str = scheme.get("institution_slug", "")
        compact_key = scheme.get("compact_key") or f"{min_rate}_{sector}_{tenure_str}_{cat_str}_{inst_str}"

        base_meta = {
            "category": str(scheme.get("category", "")),
            "institution": str(scheme.get("institution", "")),
            "institution_slug": str(scheme.get("institution_slug", "")),
            "sector": str(scheme.get("sector", "")),
            "scheme_name": str(scheme.get("scheme_name", "")),
            "scheme_slug": str(scheme.get("scheme_slug", "")),
            "compact_key": str(compact_key),
            "interest_rate_range": str(scheme.get("interest_rate_range", "N/A")),
            "benchmark": str(scheme.get("benchmark", "N/A")),
            "max_tenure_years": tenure_int,
            "max_loan_amount": str(scheme.get("max_loan_amount", "N/A")),
            "min_amount_lakhs": float(scheme.get("min_amount_lakhs", 0.0)),
            "max_amount_lakhs": float(scheme.get("max_amount_lakhs", 99999.0)),
            "processing_fee": str(fm.get("processing_fee", scheme.get("processing_fee", "N/A"))),
            "target_borrowers": str(fm.get("target_borrowers", scheme.get("target_borrowers", ""))),
            "source_url": str(scheme.get("source_url", ""))
        }

        # 1. PARENT CARD / COMPACT OVERVIEW CHUNK
        parent_card_text = (
            f"Loan Scheme: {scheme['scheme_name']} ({scheme['institution']})\n"
            f"Key Signature: {compact_key}\n"
            f"Category: {scheme['category']} | Sector: {scheme['sector']}\n"
            f"Interest Rate: {scheme.get('interest_rate_range')} ({scheme.get('benchmark')})\n"
            f"Max Quantum & Tenure: {scheme.get('max_loan_amount')}, {scheme.get('max_tenure_years')} years\n"
            f"Processing Fee: {base_meta['processing_fee']}\n"
            f"Target Borrowers: {base_meta['target_borrowers']}\n"
            f"Overview: {sections.get('summary', '')[:300]}"
        )
        parent_meta = dict(base_meta)
        parent_meta["section_type"] = "parent_card"
        doc_id_parent = f"{scheme['category']}_{scheme['institution_slug']}_{scheme['scheme_slug']}_parent".replace(" ", "_")

        documents.append(parent_card_text)
        metadatas.append(parent_meta)
        ids.append(doc_id_parent)

        # 2. CHILD SECTION CHUNKS
        for stype, scontent in sections.items():
            if stype == "summary":
                continue  # already in parent card
            if not scontent or len(scontent.strip()) < 10:
                continue

            child_text = (
                f"{scheme['scheme_name']} ({scheme['institution']}) - {stype.upper()} Details:\n"
                f"Key: {compact_key}\n"
                f"{scontent}"
            )
            child_meta = dict(base_meta)
            child_meta["section_type"] = stype
            doc_id_child = f"{scheme['category']}_{scheme['institution_slug']}_{scheme['scheme_slug']}_{stype}".replace(" ", "_")

            documents.append(child_text)
            metadatas.append(child_meta)
            ids.append(doc_id_child)

    print(f"Total chunks generated: {len(documents)}. Upserting into ChromaDB in batches of 100...")

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )
        print(f"Indexed chunks {i+1} to {end} / {len(documents)}")

    print(f"Successfully built Hierarchical ChromaDB index with {collection.count()} chunks at: {CHROMA_PATH}")

if __name__ == "__main__":
    build_index()
