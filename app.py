"""🏦 FinNav / Credence — Indian Loan Advisor AI
Built with Gradio, LangGraph, ChromaDB, and Qwen on Groq.
Ready for deployment on Hugging Face Spaces (ZeroGPU / Free CPU).
"""

import os
import uuid
import gradio as gr
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

from rag.graph import loan_advisor_graph

# Custom styling for a modern, sleek banking assistant interface
CUSTOM_CSS = """
.gradio-container {
    max-width: 1250px !important;
    margin: 0 auto !important;
}
.header-box {
    text-align: center;
    padding: 18px 0;
    margin-bottom: 12px;
}
.header-title {
    font-size: 2.1rem;
    font-weight: 700;
    color: #1E3A8A;
    margin-bottom: 4px;
}
.header-subtitle {
    font-size: 1.0rem;
    color: #4B5563;
    margin-bottom: 8px;
}
.metric-badge {
    background-color: #EEF2FF;
    border: 1px solid #C7D2FE;
    color: #3730A3;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    margin: 2px 4px;
}
"""

def user_submit(message, history):
    if not message or not message.strip():
        return "", history
    history = history or []
    history.append({"role": "user", "content": message.strip()})
    return "", history

def bot_respond(history, session_id, cibil, income, loan_amt, category, sector, emp_type, api_key, model_name):
    if not history:
        return history, ""

    last_user_query = history[-1]["content"]

    user_profile = {
        "Employment": emp_type,
        "CIBIL Score": cibil,
        "Income": income.strip() if income else None,
        "Requested Amount": loan_amt.strip() if loan_amt else None,
        "Category Filter": category if category != "All" else None,
        "Sector Filter": sector if sector != "All" else None
    }

    graph_input = {
        "chat_id": session_id,
        "query": last_user_query,
        "user_profile": user_profile,
        "api_key": api_key.strip() if api_key else None,
        "model_name": model_name.strip() if model_name else "qwen/qwen3.8-27b"
    }

    try:
        result = loan_advisor_graph.invoke(
            graph_input,
            config={"configurable": {"thread_id": session_id}}
        )

        detected_intent = result.get("intent", "RECOMMENDATION")
        final_text = result.get("final_response", "")
        candidates = result.get("candidates", [])

        intent_badges = {
            "COMPARISON": "⚖️ Scheme Comparison",
            "RECOMMENDATION": "🔍 Personalized Recommendation",
            "CONCEPT_FAQ": "📚 Banking Concept & Regulation",
            "ELIGIBILITY_QUERY": "📋 Eligibility & Criteria",
            "META_CHAT": "💬 Clarification",
            "EMI_CALCULATOR": "🧮 Exact EMI Calculation"
        }
        if detected_intent == "RECOMMENDATION" and not candidates:
            badge = "⚠️ Eligibility Advisory"
        else:
            badge = intent_badges.get(detected_intent, f"⚡ {detected_intent}")

        formatted_reply = f"**`{badge}`**\n\n{final_text}"
        history.append({"role": "assistant", "content": formatted_reply})

        # Sources markdown
        sources_md = ""
        if candidates:
            sources_md = "#### 🔍 Fact Check: Official Sources for Last Answer\n"
            for idx, c in enumerate(candidates, 1):
                m = c["metadata"]
                sources_md += f"{idx}. **{m.get('scheme_name')}** ({m.get('institution')}) — Rate: `{m.get('interest_rate_range')}` | [Official Portal]({m.get('source_url')})\n"

        return history, sources_md
    except Exception as e:
        history.append({"role": "assistant", "content": f"⚠️ An error occurred while processing: {str(e)}"})
        return history, ""

def create_new_session():
    new_id = f"chat_{uuid.uuid4().hex[:8]}"
    return new_id, [], f"🆔 Active Session: `{new_id}`", ""

def load_example(example_text):
    return example_text

with gr.Blocks(title="FinNav — Indian Loan Advisor AI") as demo:
    session_id_state = gr.State(value=f"chat_{uuid.uuid4().hex[:8]}")

    gr.HTML("""
    <div class="header-box">
        <div class="header-title">🏦 FinNav — Indian Loan Advisor AI</div>
        <div class="header-subtitle">Powered by LangGraph Agent + ChromaDB Grounded RAG + Qwen Model</div>
        <div>
            <span class="metric-badge">163 Verified Schemes</span>
            <span class="metric-badge">34 Lending Institutions</span>
            <span class="metric-badge">Zero Hallucination Guardrails</span>
            <span class="metric-badge">100% Free</span>
        </div>
    </div>
    """)

    with gr.Row():
        # Left Column: User Profile & Filter Controls
        with gr.Column(scale=1):
            with gr.Accordion("⚙️ Model & API Settings", open=False):
                api_key_input = gr.Textbox(
                    label="Groq API Key",
                    value=os.environ.get("GROQ_API_KEY", ""),
                    type="password",
                    placeholder="gsk_..."
                )
                model_name_input = gr.Textbox(
                    label="Model Name",
                    value=os.environ.get("MODEL_NAME", "qwen/qwen3.8-27b")
                )

            gr.Markdown("### 🎯 Profile & Filters")
            category_dropdown = gr.Dropdown(
                label="Loan Category Filter",
                choices=["All", "Home Loan", "Personal Loan", "Education Loan", "Vehicle Loan"],
                value="All"
            )
            sector_dropdown = gr.Dropdown(
                label="Banking Sector Filter",
                choices=["All", "Public", "Private", "NBFC", "Co-operative"],
                value="All"
            )
            emp_type_dropdown = gr.Dropdown(
                label="Employment Type",
                choices=["Salaried", "Self-Employed / Business", "Student", "Pensioner", "Doctor / Professional", "Other"],
                value="Salaried"
            )
            cibil_slider = gr.Slider(
                label="CIBIL / Credit Score",
                minimum=300,
                maximum=900,
                value=750,
                step=10
            )
            income_text = gr.Textbox(
                label="Monthly Income / Annual CTC",
                placeholder="e.g. 60,000 / month or 12k"
            )
            loan_amt_text = gr.Textbox(
                label="Loan Amount Requested",
                placeholder="e.g. 20 Lakhs or 2cr"
            )

            session_label = gr.Markdown(f"🆔 Active Session: `{session_id_state.value}`")
            new_chat_btn = gr.Button("➕ New Chat Session", variant="secondary")

            gr.Markdown("### 💡 Quick Try Prompts")
            ex1 = gr.Button("👉 Compare SBI Scholar vs Canara Vidya Turant", size="sm")
            ex2 = gr.Button("👉 What is EBLR vs MCLR and which is better?", size="sm")
            ex3 = gr.Button("👉 Calculate EMI for 20 Lakhs at 8.75% for 7 years", size="sm")
            ex4 = gr.Button("👉 Can u share the affordable housing options", size="sm")
            ex5 = gr.Button("👉 Doctor wanting flexible overdraft personal loan", size="sm")

        # Right Column: Chat Interface
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Advisor Dialogue",
                height=520
            )

            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="Ask about loans, request comparisons, check eligibility, or calculate EMIs...",
                    label="",
                    scale=5,
                    lines=1,
                    max_lines=3
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)

            clear_chat_btn = gr.Button("🗑️ Clear Screen", size="sm")

            sources_display = gr.Markdown("")

    # Interactions
    chat_inputs = [
        chatbot,
        session_id_state,
        cibil_slider,
        income_text,
        loan_amt_text,
        category_dropdown,
        sector_dropdown,
        emp_type_dropdown,
        api_key_input,
        model_name_input
    ]

    # Submit handlers
    send_btn.click(
        user_submit,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    ).then(
        bot_respond,
        inputs=chat_inputs,
        outputs=[chatbot, sources_display]
    )

    msg_input.submit(
        user_submit,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot]
    ).then(
        bot_respond,
        inputs=chat_inputs,
        outputs=[chatbot, sources_display]
    )

    clear_chat_btn.click(lambda: ([], ""), outputs=[chatbot, sources_display])

    new_chat_btn.click(
        create_new_session,
        outputs=[session_id_state, chatbot, session_label, sources_display]
    )

    # Example button clicks
    ex1.click(lambda: "Compare SBI Scholar vs Canara Vidya Turant", outputs=msg_input)
    ex2.click(lambda: "What is EBLR vs MCLR and which is better?", outputs=msg_input)
    ex3.click(lambda: "Calculate EMI for 20 Lakhs at 8.75% for 7 years", outputs=msg_input)
    ex4.click(lambda: "can u share the affordable housing options", outputs=msg_input)
    ex5.click(lambda: "Doctor wanting flexible overdraft personal loan", outputs=msg_input)

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=CUSTOM_CSS)
