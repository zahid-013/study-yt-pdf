# Shared utilities for the Study app
import re
import streamlit as st
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from Projects.study_config import LLM_CONFIG, EMBEDDINGS_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


@st.cache_resource
def load_llm():
    """Load and cache the LLM"""
    llm = HuggingFaceEndpoint(**LLM_CONFIG)
    return ChatHuggingFace(llm=llm)


@st.cache_resource
def load_embeddings():
    """Load and cache embeddings model"""
    return HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)


def get_text_splitter():
    """Get configured text splitter"""
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )


def format_docs(docs: List) -> str:
    """Format documents for context"""
    return "\n\n".join(doc.page_content for doc in docs)


def extract_youtube_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    pattern = r"(?:v=|youtu.be/)([a-zA-Z0-9_-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None


def create_youtube_prompt() -> PromptTemplate:
    """Create prompt for YouTube mode"""
    return PromptTemplate(
        template="""You are a helpful assistant.
Answer ONLY from the provided transcript context.
If the context is insufficient, just say 'This information is not available in the provided context.'

{context}
Question: {question}""",
        input_variables=['context', 'question'],
    )


def create_pdf_prompt() -> PromptTemplate:
    """Create prompt for PDF mode"""
    return PromptTemplate(
        template="""You are a helpful assistant. Answer the question based on the provided context.

Context: {context}

Chat History: {history}

Question: {question}

Answer:""",
        input_variables=['context', 'history', 'question'],
    )
