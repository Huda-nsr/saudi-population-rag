"""
app.py — the clickable demo. Run it with:  python app.py
Then open the local URL it prints. This is what you deploy to Hugging Face Spaces.

The two example buttons (one English, one Arabic) matter: they let a reviewer see
the bilingual capability in one click, without having to type Arabic themselves.
"""
import gradio as gr
from src.rag import answer


def respond(question):
    """Called when the user submits. Formats the answer + a visible source line."""
    if not question.strip():
        return "Please type a question first."

    result = answer(question)
    text = result["answer"]
    src = result["source"]

    # Always show the source — this is the 'grounding' that makes RAG trustworthy.
    if src and src.get("dataset"):
        text += f"\n\n---\n**Source:** {src['dataset']}"
        if src.get("url"):
            text += f"  \n{src['url']}"
        text += f"  \n*(answering path: {src['path_used']})*"
        if src.get("sample_data"):
            text += ("  \n⚠️ *Demo figures are synthetic sample data; the cited "
                     "dataset page is real. Download the real CSV to use actual values.*")
    return text


# Build a simple, clean interface.
with gr.Blocks(title="Saudi Population & Census — Q&A") as demo:
    gr.Markdown(
        "# 🇸🇦 Saudi Population & Census — Q&A\n"
        "Ask about Saudi population and census data in **English or Arabic**. "
        "Every answer cites the dataset it came from."
    )
    question = gr.Textbox(label="Your question", placeholder="e.g. What was the population of the Riyadh region in 2022?")
    output = gr.Markdown(label="Answer")
    ask_btn = gr.Button("Ask", variant="primary")

    # One-click bilingual examples so reviewers instantly see it works both ways.
    gr.Examples(
        examples=[
            ["What was the population of the Riyadh region in 2022?"],
            ["كم عدد سكان منطقة مكة المكرمة؟"],
        ],
        inputs=question,
    )

    ask_btn.click(fn=respond, inputs=question, outputs=output)
    question.submit(fn=respond, inputs=question, outputs=output)


if __name__ == "__main__":
    demo.launch()
