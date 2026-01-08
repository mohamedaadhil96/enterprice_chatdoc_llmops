import os
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from multi_doc_chat.src.document_ingestion.data_ingestion import ChatIngestor
from multi_doc_chat.src.document_chat.retrieval import ConversationalRAG
from langchain_core.messages import HumanMessage, AIMessage
from multi_doc_chat.exception.custom_exception import DocumentPortalException
from multi_doc_chat.utils.session_store import session_store
from multi_doc_chat.utils.auth import (
    user_store, 
    create_access_token, 
    get_current_user, 
    user_to_response,
    UserCreate, 
    UserLogin, 
    UserResponse, 
    TokenResponse
)
from multi_doc_chat.utils.models import User
from multi_doc_chat.utils.db import init_db


# ----------------------------
# Configuration
# ----------------------------
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173,http://127.0.0.1:5173").split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB default
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ----------------------------
# Rate Limiter
# ----------------------------
limiter = Limiter(key_func=get_remote_address)


# ----------------------------
# Lifecycle Events
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and clean up expired sessions
    init_db()
    expired = session_store.cleanup_expired()
    if expired > 0:
        print(f"Cleaned up {expired} expired sessions on startup")
    yield
    # Shutdown: nothing special needed


# ----------------------------
# FastAPI initialization
# ----------------------------
app = FastAPI(
    title="Lumina AI",
    version="2.0.0",
    description="Enterprise Document Intelligence Platform",
    lifespan=lifespan
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Static and templates
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))


# ----------------------------
# Adapters
# ----------------------------
class FastAPIFileAdapter:
    """Adapt FastAPI UploadFile to a simple object with .name and .getbuffer()."""
    def __init__(self, uf: UploadFile):
        self._uf = uf
        self.name = uf.filename or "file"

    def getbuffer(self) -> bytes:
        self._uf.file.seek(0)
        return self._uf.file.read()


# ----------------------------
# Models
# ----------------------------
class UploadResponse(BaseModel):
    session_id: str
    indexed: bool
    message: Optional[str] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str


# ----------------------------
# Input Validation Helpers
# ----------------------------
def validate_file(file: UploadFile) -> None:
    """Validate file size and extension."""
    # Check extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (read and check)
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File '{filename}' exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )


# ----------------------------
# Auth Routes
# ----------------------------
@app.post("/auth/signup", response_model=UserResponse)
def signup(user_in: UserCreate):
    """Register a new user."""
    try:
        user = user_store.create(user_in.email, user_in.password, user_in.name)
        return user_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/signin", response_model=TokenResponse)
def signin(login: UserLogin):
    """Authenticate and return JWT token."""
    user = user_store.authenticate(login.email, login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": user.id})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_to_response(user)
    )


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return user_to_response(current_user)


@app.get("/sessions")
def list_sessions(current_user: User = Depends(get_current_user)):
    """List all sessions belonging to the current user."""
    user_id = current_user.id
    sessions = session_store.get_user_sessions(user_id)
    print(f"DEBUG: Listing sessions for user {user_id}: found {len(sessions)}")
    return sessions


# ----------------------------
# Application Routes
# ----------------------------
@app.get("/health")
def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "ChatDocAI"
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    """Serve the main application page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_model=UploadResponse)
@limiter.limit("5/minute")
async def upload(
    request: Request, 
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
) -> UploadResponse:
    """
    Upload and index documents.
    Requires authentication.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    # Validate all files first
    for f in files:
        validate_file(f)

    try:
        # Wrap FastAPI files to preserve filename/ext and provide a read buffer
        wrapped_files = [FastAPIFileAdapter(f) for f in files]

        ingestor = ChatIngestor(use_session_dirs=True)
        session_id = ingestor.session_id

        # Save, load, split, embed, and write FAISS index with MMR
        ingestor.built_retriver(
            uploaded_files=wrapped_files,
            search_type="mmr",
            fetch_k=20,
            lambda_mult=0.5
        )

        # Create persistent session with user owner
        filenames = [f.filename for f in files]
        print(f"DEBUG: Creating session {session_id} for user {current_user.id} with files {filenames}")
        session_store.create(session_id, current_user.id, filenames=filenames)

        return UploadResponse(session_id=session_id, indexed=True, message="Indexing complete")
    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request, 
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    Chat with uploaded documents.
    Requires authentication.
    """
    session_id = req.session_id
    message = req.message.strip()
    
    if not session_id or not session_store.exists(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id. Re-upload documents.")
    
    # Check session ownership
    if session_store.get_owner(session_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Build RAG and load retriever from persisted FAISS with MMR
        rag = ConversationalRAG(session_id=session_id)
        index_path = f"faiss_index/{session_id}"
        rag.load_retriever_from_faiss(
            index_path=index_path,
            search_type="mmr",
            fetch_k=20,
            lambda_mult=0.5
        )

        # Get chat history from persistent storage
        history = session_store.get_history(session_id)
        lc_history = []
        for m in history:
            role = m.get("role")
            content = m.get("content", "")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))

        answer = rag.invoke(message, chat_history=lc_history)

        # Save to persistent history
        session_store.add_message(session_id, "user", message)
        session_store.add_message(session_id, "assistant", answer)

        return ChatResponse(answer=answer)
    except DocumentPortalException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")


# Uvicorn entrypoint
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
