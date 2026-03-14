# src/app.py (updated)
import streamlit as st
import jwt
from src.auth.auth_service import signup, login
from src.llm.rag import answer
from src.db.mongo import create_chat, append_message, get_chat_history, list_chats_for_user
from src.llm.providers import get_llm_provider
from src.llm.embeddings import get_embeddings
from src.config import settings

st.set_page_config(page_title="Ultima Assistant", page_icon="🤖", layout="wide")

def get_session_user():
    token = st.session_state.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        return None

with st.sidebar:
    st.title("Account")
    mode = st.radio("Auth", ["Login", "Sign up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button(mode):
        try:
            if mode == "Sign up":
                signup(email, password)
                st.success("Account created. Please login.")
            else:
                token = login(email, password)
                st.session_state["token"] = token
                st.success("Logged in.")
        except Exception as e:
            st.error(str(e))
    if st.button("Logout"):
        st.session_state.pop("token", None)

user = get_session_user()
st.title("AI Assistant with RAG")
if not user:
    st.info("Please login to start a chat.")
    st.stop()

# Model selections
st.sidebar.markdown("---")
st.sidebar.subheader("Models")
llm_provider_name = st.sidebar.selectbox("LLM provider", ["openai", "ollama"], index=0)
llm_model = st.sidebar.text_input("LLM model", value="gpt-4o-mini" if llm_provider_name=="openai" else "llama3")
emb_provider_name = st.sidebar.selectbox("Embeddings provider", ["openai", "ollama", "sentence-transformers"], index=0)
emb_model = st.sidebar.text_input("Embeddings model", value="text-embedding-3-small" if emb_provider_name=="openai" else "all-MiniLM-L6-v2")

# Cache provider instances per selection
@st.cache_resource
def _get_llm_provider_cached(name: str):
    return get_llm_provider(name)

@st.cache_resource
def _get_embeddings_cached(provider: str, model: str):
    return get_embeddings(provider, model)

llm_provider = _get_llm_provider_cached(llm_provider_name)
embeddings = _get_embeddings_cached(emb_provider_name, emb_model)

# Chat session management
st.sidebar.subheader("Chats")
chats = list_chats_for_user(user_id=user["sub"])
titles = [f"{c['title']} ({str(c['_id'])[-6:]})" for c in chats]
selected = st.sidebar.selectbox("Select chat", options=["New chat"] + titles, index=0)

st.sidebar.subheader("Generation Settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
top_k = st.sidebar.number_input("Top K documents", min_value=1, max_value=10, value=3)
threshold = st.sidebar.slider("Score threshold", 0.0, 1.0, 0.75, 0.05)



def ensure_chat():
    if "chat_id" not in st.session_state or selected == "New chat":
        st.session_state["chat_id"] = create_chat(user_id=user["sub"], title="Untitled")
    else:
        idx = titles.index(selected)
        st.session_state["chat_id"] = str(chats[idx]["_id"])
ensure_chat()

# Upload and ingest documents (pdf, docx, txt)
st.header("Knowledge base")
uploaded = st.file_uploader("Upload files", type=["txt","pdf","docx"], accept_multiple_files=True)
if uploaded:
    import tempfile, os
    from src.data.ingest import reindex_if_changed
    for f in uploaded:
        suffix = os.path.splitext(f.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.read())
            from src.data.loaders import load_any
            text, mime = load_any(tmp.name)
            doc_id = f"{user['sub']}::{f.name}"
            changed_count = reindex_if_changed(doc_id, text, source_name=f.name, user_id=user["sub"], mime_type=mime)
            if changed_count == 0:
                st.info(f"No changes detected in {f.name}.")
            else:
                st.success(f"Indexed {changed_count} chunks from {f.name}.")
        os.unlink(tmp.name)

# Display past messages for continuous chat
st.header("Chat")
history = get_chat_history(st.session_state["chat_id"])
for m in history:
    role = "User" if m["role"] == "user" else "Assistant"
    st.markdown(f"**{role}:** {m['content']}")

question = st.text_input("Ask a question")
if st.button("Send") and question.strip():
    append_message(st.session_state["chat_id"], "user", question)
    with st.spinner("Thinking..."):
        resp = answer(
            question,
            llm_provider=llm_provider,
            llm_model=llm_model,
            embeddings=embeddings,
            user_id=user["sub"],
            top_k=top_k,
            threshold=threshold,
            temperature=temperature
        )
    append_message(st.session_state["chat_id"], "assistant", resp["answer"], sources=[c["source"] for c in resp["contexts"]])
    st.markdown(resp["answer"])
    with st.expander("Sources"):
        for c in resp["contexts"]:
            st.write(f"- {c['source']} (score: {c['score']:.3f})")


        