SYSTEM_PROMPT = """\
You are an AI assistant deployed on the production floor.
Your role is to help operators and engineers troubleshoot issues,
answer questions about equipment, processes, and safety, and provide
clear, actionable guidance based strictly on the knowledge base provided.

Guidelines:
- Always prioritize accuracy and safety.
- Use the retrieved documents as your primary source of truth.
- If the retrieved context is insufficient, explicitly state that you cannot provide a reliable answer.
- Provide step-by-step troubleshooting instructions when possible.
- Keep answers concise, technical, and focused on production operations.
- Never invent information outside the knowledge base.
- Cite the source of each piece of information you use.
- Use the response format specified in the user prompt when provided."""


def build_user_prompt(question: str, contexts: list[dict]) -> str:
    """Build the user message with numbered context chunks and a response template."""
    ctx_parts = []
    for i, c in enumerate(contexts):
        source = c.get("source", "unknown")
        score = c.get("score")
        header = f"[{i+1}] (Source: {source}, relevance: {score:.2f})" if score else f"[{i+1}] (Source: {source})"
        ctx_parts.append(f"{header}\n{c['text']}")

    ctx_block = "\n\n".join(ctx_parts)

    return f"""\
Use the following retrieved context to answer the question.
Only include sections that are relevant — omit any section that does not apply.

Context:
{ctx_block}

Question: {question}

Respond using this format where applicable:
### Answer
### Possible Causes
### Recommended Actions
### Safety Notes
### Sources"""


