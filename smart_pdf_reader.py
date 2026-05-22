import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


llm = HuggingFaceEndpoint(
    repo_id='meta-llama/Llama-3.3-70B-Instruct',
    task='text-generation',
    temperature=0.5
)

model = ChatHuggingFace(llm=llm)

# Set page config
st.set_page_config(page_title="Smart PDF Reader", page_icon="📄")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False
if "splits" not in st.session_state:
    st.session_state.splits = None

# Sidebar for actions
with st.sidebar:
    st.title("📄 Smart PDF Reader")
    uploaded_file = st.file_uploader("Drop your PDF here", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Load PDF"):
            with st.spinner("Loading PDF..."):
                # Save uploaded file temporarily
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                loader = PyPDFLoader("temp.pdf")
                docs = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                st.session_state.splits = text_splitter.split_documents(docs)
                st.session_state.docs_loaded = True
                st.success("PDF loaded successfully!")
        
        if st.session_state.docs_loaded:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
            
            if st.button("Summarize PDF"):
                with st.spinner("Summarizing..."):
                    context_text = " ".join([doc.page_content for doc in st.session_state.splits])
                    
                    summary_template = PromptTemplate.from_template(
                        """Provide a concise summary of the following document.\n
                        \nDocument: {context}\n
                        \nSummary:"""
                    )
                    
                    chain = summary_template | model | StrOutputParser()
                    summary = chain.invoke({"context": context_text[:5000]})
                    st.session_state.summary = summary

# Main content
st.title("📄 Smart PDF Reader")

if not st.session_state.docs_loaded:
    st.info("Please upload a PDF file from the sidebar to get started.")
else:
    # Show summary if available
    if "summary" in st.session_state:
        with st.expander("📝 Document Summary", expanded=True):
            st.write(st.session_state.summary)
    
    # Chat interface
    st.subheader("💬 Chat about your PDF")
    
    # Display chat history
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)
    
    # Chat input
    if prompt := st.chat_input("Ask a question about the PDF..."):
        # Add user message to history
        st.session_state.chat_history.append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get relevant context (top 3 chunks)
                context_text = " ".join([doc.page_content for doc in st.session_state.splits[:3]])
                
                chat_template = ChatPromptTemplate.from_template(
                    """You are a helpful assistant. Answer the question based on the provided context.
                    \nContext: {context}\n
                    \nChat History: {history}\n
                    \nQuestion: {question}\n
                    \nAnswer:"""
                )
                
                history_text = "\n".join(
                    [f"User: {m}" if r == "user" else f"Assistant: {m}" 
                     for r, m in st.session_state.chat_history[-5:]]
                )
                
                chain = chat_template | model | StrOutputParser()
                
                response = chain.invoke({
                    "context": context_text,
                    "history": history_text,
                    "question": prompt
                })
                
                st.markdown(response)
                st.session_state.chat_history.append(("assistant", response))