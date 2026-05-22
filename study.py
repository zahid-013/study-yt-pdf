"""
Smart Study - Unified YouTube Chatbot & PDF Reader
A merged application combining YouTube transcript analysis and PDF document interaction
with persistent database storage and multi-threaded processing.
"""

import streamlit as st
from pathlib import Path
import sys

from study_config import K_RETRIEVER

# Add project root to path so top-level package imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import mode modules (we'll handle inline for now due to directory structure)
from study_config import *
from study_db import StudyDB

# Page configuration
st.set_page_config(
    page_title="Smart Study - Chat with Documents",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .block-container { max-width: 1000px; }
    [data-testid="stSidebar"] { min-width: 320px; }
    .mode-header { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 12px;
        font-size: 0.85rem; font-weight: 600;
    }
    .badge-ready  { background: #d4edda; color: #155724; }
    .badge-idle   { background: #fff3cd; color: #856404; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "youtube"

# Sidebar - Mode Switcher
st.sidebar.markdown("# 🧠🎬📚 Smart Study")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Choose Mode",
    ["🎬 YouTube Chatbot", "📄 PDF Reader"],
    key="mode_selector"
)

st.session_state.current_mode = "youtube" if "🎬" in mode else "pdf"

st.sidebar.markdown("---")

# Initialize database
db = StudyDB()

# Mode 1: YouTube Chatbot
if st.session_state.current_mode == "youtube":
    # Import inline to avoid directory issues
    from concurrent.futures import ThreadPoolExecutor
    from langchain_community.vectorstores import FAISS
    from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
    
    from study_utils import (
        load_llm, load_embeddings, format_docs, 
        extract_youtube_video_id, create_youtube_prompt, get_text_splitter
    )

    # Initialize YouTube session state
    if "yt_video_loaded" not in st.session_state:
        st.session_state.yt_video_loaded = False
        st.session_state.yt_video_id = None
        st.session_state.yt_messages = []
        st.session_state.yt_vector_store = None
        st.session_state.yt_transcript = None

    def fetch_youtube_transcript(video_id: str) -> tuple:
        """Fetch YouTube transcript with threading"""
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id)
        transcript = " ".join(snippet.text for snippet in transcript_data)
        
        splitter = get_text_splitter()
        chunks = splitter.split_text(transcript)
        
        vector_store = FAISS.from_texts(chunks, load_embeddings())
        return vector_store, transcript

    # YouTube mode UI
    st.markdown("### ▶️ YouTube Video Chatbot")
    st.caption("Paste a YouTube link, load the transcript, and ask anything about the video.")

    # Sidebar controls
    st.sidebar.markdown("#### 🎬 Video Setup")
    yt_link = st.sidebar.text_input(
        "YouTube Video URL",
        placeholder="youtube....",
        key="yt_input"
    )
    
    col1, col2 = st.sidebar.columns(2)
    load_btn = col1.button("🔍 Load", use_container_width=True, key="yt_load")
    clear_btn = col2.button("🗑️ Clear", use_container_width=True, key="yt_clear")

    # Handle load button
    if load_btn and yt_link:
        video_id = extract_youtube_video_id(yt_link)
        if not video_id:
            st.sidebar.error("⚠️ Invalid YouTube URL.")
        else:
            if video_id != st.session_state.yt_video_id:
                st.session_state.yt_messages = []

            try:
                with st.spinner("🔄 Fetching transcript & building index..."):
                    # Try cache first
                    cached = db.get_cached_video(video_id)
                    if cached:
                        transcript = cached['transcript']
                        splitter = get_text_splitter()
                        chunks = splitter.split_text(transcript)
                        vector_store = FAISS.from_texts(chunks, load_embeddings())
                        st.sidebar.info("📦 Loaded from cache")
                    else:
                        # Fetch with threading
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(fetch_youtube_transcript, video_id)
                            vector_store, transcript = future.result()
                        db.cache_video(video_id, yt_link, transcript)

                st.session_state.yt_video_loaded = True
                st.session_state.yt_video_id = video_id
                st.session_state.yt_vector_store = vector_store
                st.session_state.yt_transcript = transcript
                st.sidebar.success("✅ Transcript loaded!")

            except TranscriptsDisabled:
                st.sidebar.error("🚫 No captions available for this video.")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)[:100]}")

    if clear_btn:
        st.session_state.yt_messages = []
        st.session_state.yt_video_loaded = False
        db.clear_chat_history("youtube")
        st.rerun()

    # Display video info
    if st.session_state.yt_video_loaded:
        st.sidebar.markdown('<span class="status-badge badge-ready">✅ Ready</span>', unsafe_allow_html=True)

        if st.session_state.yt_video_id:
            st.sidebar.image(
                f"https://img.youtube.com/vi/{st.session_state.yt_video_id}/hqdefault.jpg",
                use_container_width=True
            )

        if st.session_state.yt_transcript:
            with st.sidebar.expander("📜 Show transcript"):
                st.write(st.session_state.yt_transcript)

        # Chat interface
        st.divider()
        for msg in st.session_state.yt_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Ask a question about the video...", key="yt_chat"):
            st.session_state.yt_messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            db.add_chat_message("youtube", "user", user_query)

            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        model = load_llm()
                        retriever = st.session_state.yt_vector_store.as_retriever(
                            search_type="similarity", 
                            search_kwargs={"k": K_RETRIEVER}
                        )
                        
                        prompt = create_youtube_prompt()
                        parallel_chain = RunnableParallel({
                            'context': retriever | RunnableLambda(format_docs),
                            'question': RunnablePassthrough(),
                        })
                        chain = parallel_chain | prompt | model | StrOutputParser()
                        
                        result = chain.invoke(user_query)
                        st.write(result)
                        db.add_chat_message("youtube", "assistant", result)
                        st.session_state.yt_messages.append({"role": "assistant", "content": result})
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    else:
        st.info("👈 Paste a YouTube video URL in the sidebar and click **Load** to get started.")


# Mode 2: PDF Reader
else:
    import tempfile
    from concurrent.futures import ThreadPoolExecutor
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate
    
    from study_utils import load_llm, get_text_splitter, create_pdf_prompt

    # Initialize PDF session state
    if "pdf_chat_history" not in st.session_state:
        st.session_state.pdf_chat_history = []
    if "pdf_docs_loaded" not in st.session_state:
        st.session_state.pdf_docs_loaded = False
    if "pdf_splits" not in st.session_state:
        st.session_state.pdf_splits = None
    if "pdf_summary" not in st.session_state:
        st.session_state.pdf_summary = None
    if "pdf_filename" not in st.session_state:
        st.session_state.pdf_filename = None

    def process_pdf(file_path: str):
        """Process PDF file with threading"""
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        splitter = get_text_splitter()
        splits = splitter.split_documents(docs)
        return splits

    def generate_pdf_summary(splits):
        """Generate PDF summary"""
        context_text = " ".join([doc.page_content for doc in splits])
        model = load_llm()
        
        summary_prompt = PromptTemplate.from_template(
            """Provide a concise summary of the following document.

Document: {context}

Summary:"""
        )
        
        chain = summary_prompt | model | StrOutputParser()
        summary = chain.invoke({"context": context_text[:5000]})
        return summary

    # PDF mode UI
    st.markdown("### 📄 Smart PDF Reader")
    st.caption("Upload a PDF and chat about its contents.")

    # Sidebar controls
    with st.sidebar:
        st.markdown("#### 📄 PDF Setup")
        uploaded_file = st.file_uploader("Drop your PDF here", type=["pdf"], key="pdf_upload")
        
        if uploaded_file is not None:
            if st.button("Load PDF", use_container_width=True, key="pdf_load"):
                with st.spinner("📖 Loading PDF..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.getbuffer())
                            tmp_path = tmp.name

                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(process_pdf, tmp_path)
                            splits = future.result()

                        st.session_state.pdf_splits = splits
                        st.session_state.pdf_docs_loaded = True
                        st.session_state.pdf_filename = uploaded_file.name
                        db.add_upload("pdf", uploaded_file.name, tmp_path)
                        st.success("✅ PDF loaded successfully!")
                    except Exception as e:
                        st.error(f"❌ Error loading PDF: {str(e)[:100]}")

            if st.session_state.pdf_docs_loaded:
                if st.button("Clear Chat", use_container_width=True, key="pdf_clear"):
                    st.session_state.pdf_chat_history = []
                    st.session_state.pdf_summary = None
                    db.clear_chat_history("pdf")
                    st.rerun()

                if st.button("Summarize PDF", use_container_width=True, key="pdf_summarize"):
                    with st.spinner("✍️ Generating summary..."):
                        try:
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                future = executor.submit(generate_pdf_summary, st.session_state.pdf_splits)
                                summary = future.result()
                            st.session_state.pdf_summary = summary
                        except Exception as e:
                            st.error(f"❌ Error generating summary: {str(e)[:100]}")

    # Main content
    if not st.session_state.pdf_docs_loaded:
        st.info("👈 Upload a PDF file from the sidebar to get started.")
    else:
        st.divider()

        if st.session_state.pdf_summary:
            with st.expander("📝 Document Summary", expanded=True):
                st.write(st.session_state.pdf_summary)

        st.subheader("💬 Chat about your PDF")

        for role, message in st.session_state.pdf_chat_history:
            with st.chat_message(role):
                st.markdown(message)

        if prompt := st.chat_input("Ask a question about the PDF...", key="pdf_chat"):
            st.session_state.pdf_chat_history.append(("user", prompt))
            with st.chat_message("user"):
                st.markdown(prompt)
            db.add_chat_message("pdf", "user", prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        model = load_llm()
                        context_text = " ".join([doc.page_content for doc in st.session_state.pdf_splits[:3]])
                        
                        history_text = "\n".join(
                            [f"User: {m}" if r == "user" else f"Assistant: {m}" 
                             for r, m in st.session_state.pdf_chat_history[-MAX_HISTORY_CONTEXT:]]
                        )
                        
                        prompt_template = create_pdf_prompt()
                        chain = prompt_template | model | StrOutputParser()
                        
                        response = chain.invoke({
                            "context": context_text,
                            "history": history_text,
                            "question": prompt
                        })
                        
                        st.markdown(response)
                        db.add_chat_message("pdf", "assistant", response)
                        st.session_state.pdf_chat_history.append(("assistant", response))
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
