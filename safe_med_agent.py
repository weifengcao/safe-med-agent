from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import ahocorasick

# Emergency words list
EMERGENCY_WORDS = [
    "suicide",
    "homicide",
    "kill",
    "danger",
    "emergency",
    "overdose",
    "cardiac arrest"
]

# Build Aho-Corasick Automaton
automaton = ahocorasick.Automaton()
for word in EMERGENCY_WORDS:
    automaton.add_word(word.lower(), word.lower())
automaton.make_automaton()

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app = FastAPI()
app.add_middleware(RequestIdMiddleware)

class ClinicalNoteRequest(BaseModel):
    patient_id: str
    note: str = Field(..., max_length=100000, description="The clinical note content")

class ClinicalNoteResponse(BaseModel):
    summary: str
    request_id: str

class ErrorResponse(BaseModel):
    error: str

@app.post("/v1/summarize", response_model=ClinicalNoteResponse, responses={451: {"model": ErrorResponse}})
async def summarize_note(request: Request, note_request: ClinicalNoteRequest):
    note_lower = note_request.note.lower()
    
    # Check for emergency words using Aho-Corasick
    # iter() returns an iterator of (end_index, value) tuples
    try:
        next(automaton.iter(note_lower))
        # If we reach here, a match was found
        return JSONResponse(
            status_code=451,
            content={"error": "Emergency protocol triggered"}
        )
    except StopIteration:
        # No match found
        pass
            
    # Normal processing (Mock)
    return ClinicalNoteResponse(
        summary="Normal clinical encounter",
        request_id=request.state.request_id
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}
