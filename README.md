# 📚 Study - Unified Document Chat Application

A merged, production-ready application combining **YouTube Transcript Analysis** and **PDF Document Chat** with persistent database storage, multi-threaded processing, and a seamless switchable interface.

## Features

✨ **Dual Mode Interface**
- 🎬 **YouTube Chatbot**: Extract transcripts and chat about video content
- 📄 **PDF Reader**: Upload PDFs and discuss their contents
- 🔘 **Mode Switcher**: Easy toggle between modes in the sidebar

⚡ **Threading & Performance**
- Non-blocking transcript fetching and PDF processing
- Background thread pools prevent UI freezing
- Smooth async operations with spinner feedback

💾 **Persistent Database** (SQLite)
- Store chat history for both modes
- Cache YouTube transcripts for instant reload
- Track file uploads with metadata
- Session management for users

🧠 **AI-Powered**
- Meta Llama 3.3 70B Instruct LLM
- BAAI BGE embeddings for semantic search
- RAG (Retrieval-Augmented Generation) chains
- Smart context retrieval and summarization

## Project Structure

```
Projects/
├── study.py                    # Main Streamlit app with mode switcher
├── study_db.py                 # SQLite database handler
├── study_config.py             # Shared configuration & constants
├── study_utils.py              # Shared utilities (LLM, embeddings, prompts)
├── requirements.txt            # Python dependencies
├── study.db                    # SQLite database (auto-created)
└── README.md                   # This file
```

## Installation

1. **Clone/Download** the project to your local machine

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** - Create a `.env` file in the project root:
   ```env
   HUGGINGFACEHUB_API_TOKEN=your_hugging_face_api_token
   ```

   Get your API token from [Hugging Face](https://huggingface.co/settings/tokens)

## Running the Application

Start the Streamlit app from the Projects directory:

```bash
cd Projects
streamlit run study.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### 🎬 YouTube Mode

1. **Select YouTube Mode** from the sidebar radio button
2. **Paste a YouTube URL** (with captions) in the input field
3. **Click Load** to fetch and process the transcript
   - First load processes the transcript (may take 30-60 seconds)
   - Subsequent loads use cached transcripts (instant)
4. **Ask Questions** about the video content in the chat interface
5. **View Transcript** in the sidebar expander to see the full text

**Example Questions**:
- "What are the main topics covered?"
- "Explain the technical concept mentioned at timestamp XYZ"
- "Summarize the key takeaways"

### 📄 PDF Mode

1. **Select PDF Mode** from the sidebar radio button
2. **Upload a PDF** using the file uploader
3. **Click Load PDF** to process the document
4. **Optionally Summarize** with the "Summarize PDF" button
5. **Ask Questions** about the PDF in the chat interface

**Features**:
- Automatic text splitting for large documents
- Context-aware Q&A using semantic search
- Chat history with previous context
- Document summarization

**Example Questions**:
- "What is this document about?"
- "Summarize chapter 3"
- "List the key findings"

## Database Schema

### Tables

**chat_history**
- `id`: Auto-increment primary key
- `mode`: "youtube" or "pdf"
- `role`: "user" or "assistant"
- `content`: Message text
- `timestamp`: Creation timestamp
- `metadata`: JSON metadata

**uploads**
- `id`: Auto-increment primary key
- `mode`: "youtube" or "pdf"
- `filename`: Original filename
- `file_path`: Local file path
- `upload_time`: Upload timestamp
- `processed`: Boolean flag
- `metadata`: JSON metadata

**videos**
- `id`: Auto-increment primary key
- `video_id`: YouTube video ID (unique)
- `url`: Full YouTube URL
- `title`: Video title (optional)
- `transcript`: Full transcript text
- `cached_at`: Cache timestamp
- `metadata`: JSON metadata

**sessions**
- `id`: Auto-increment primary key
- `mode`: "youtube" or "pdf"
- `resource_id`: Reference to resource (video_id or file_id)
- `created_at`: Session creation timestamp
- `updated_at`: Last activity timestamp
- `metadata`: JSON metadata

## Configuration

Edit `study_config.py` to customize:

```python
# LLM Model
LLM_CONFIG = {
    "repo_id": "meta-llama/Llama-3.3-70B-Instruct",  # Change model here
    "task": "text-generation",
    "temperature": 0.5,  # Adjust creativity (0-1)
}

# Text Processing
CHUNK_SIZE = 1000           # Document chunk size
CHUNK_OVERLAP = 200         # Overlap between chunks

# Embeddings
EMBEDDINGS_MODEL = "BAAI/bge-small-en-v1.5"  # Embedding model

# Threading
MAX_WORKERS = 3             # Thread pool size

# Chat
K_RETRIEVER = 4             # Number of context chunks to retrieve
MAX_HISTORY_CONTEXT = 5     # Messages to use as context
```

## Threading Implementation

Both modes use Python's `concurrent.futures.ThreadPoolExecutor`:

**YouTube Mode**:
- Transcript fetching runs in a background thread
- Non-blocking UI during processing
- Database cache prevents re-fetching

**PDF Mode**:
- PDF loading and processing in background threads
- Summarization runs async
- UI remains responsive

This prevents the Streamlit app from freezing during long-running operations.

## API Keys & Authentication

### Hugging Face API

1. Create account at [huggingface.co](https://huggingface.co)
2. Go to [Settings → Tokens](https://huggingface.co/settings/tokens)
3. Create a new access token (read permission)
4. Add to `.env` file:
   ```env
   HUGGINGFACEHUB_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```

### YouTube

No API key required! Uses the public YouTube Transcript API.

## Dependencies

See `requirements.txt` for complete list:

- **streamlit**: Web UI framework
- **langchain**: LLM orchestration
- **langchain-community**: PDF/document loaders
- **langchain-huggingface**: HF model integration
- **youtube-transcript-api**: YouTube transcript fetching
- **faiss-cpu**: Vector database for similarity search
- **python-dotenv**: Environment variable management

## Troubleshooting

### "No captions available for this video"
- YouTube video doesn't have auto-generated or manual captions
- Try a different video

### Slow transcript loading
- First load of a video processes and caches the transcript
- Check internet connection
- Consider using smaller model (change `LLM_CONFIG` in `study_config.py`)

### Out of memory errors
- Reduce `CHUNK_SIZE` in `study_config.py`
- Use a smaller embeddings model
- Process smaller PDF files

### Database locked
- Close other instances of the app
- Delete `study.db` to reset (will clear history)

### PDF won't load
- Check PDF is not corrupted
- Try extracting text with another tool first
- Ensure PDF is not password-protected

## Performance Tips

1. **Cache YouTube transcripts**: Don't re-fetch videos you've already loaded
2. **Adjust chunk size**: Larger chunks = fewer retrievals but broader context
3. **Limit history context**: Reduce `MAX_HISTORY_CONTEXT` for faster inference
4. **Use GPU**: If available, use `faiss-gpu` instead of `faiss-cpu`

## Future Enhancements

- [ ] Web search integration for real-time facts
- [ ] Multi-document chat (compare across PDFs)
- [ ] Audio/video file support
- [ ] Export conversations to PDF/Markdown
- [ ] User authentication & cloud sync
- [ ] Custom model fine-tuning
- [ ] API endpoint for programmatic access

## License

MIT License - Feel free to use, modify, and distribute.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review database/config files
3. Check console output for error messages
4. Verify API keys and internet connection

## Technical Architecture

```
Streamlit App (study.py)
    ├── Mode Selector (Radio Button)
    │
    ├─→ YouTube Mode
    │   ├── URL Input & Validation
    │   ├── ThreadPool: Fetch Transcript
    │   ├── Vector Store: FAISS Embeddings
    │   ├── RAG Chain: Retriever + LLM
    │   └── Database: Cache & Chat History
    │
    └─→ PDF Mode
        ├── File Upload & Validation
        ├── ThreadPool: Load & Split PDF
        ├── Text Splitting: RecursiveCharacter
        ├── RAG Chain: Retriever + LLM
        └── Database: Upload & Chat History

Database (SQLite)
    ├── chat_history (both modes)
    ├── uploads (PDF mode)
    ├── videos (YouTube mode cache)
    └── sessions (user sessions)
```

---

**Built with ❤️ using LangChain, Streamlit, and Open Source Models**
