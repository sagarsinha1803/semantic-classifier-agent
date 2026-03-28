"""
main.py — Standalone FastAPI app for Semantic Classifier Agent.
Endpoints:
  GET  /health    — health check
  POST /classify  — classify input text
"""

import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from classifier_agent.agent import root_agent

app = FastAPI(
    title="Semantic Classifier Agent",
    version="1.0.0",
    description="Classifies input text by sentiment and intent using Gemini.",
)

APP_NAME = "semantic_classifier_agent"

# ── Schemas ───────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    text: str
    model_config = {
        "json_schema_extra": {
            "examples": [{"text": "Your support team never replies to my emails!"}]
        }
    }

class ClassifyResponse(BaseModel):
    sentiment: str
    intent: str
    confidence: float
    reasoning: str

# ── Helper ────────────────────────────────────────────────────────────────────

async def run_classifier(text: str) -> dict:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id="api_user",
        session_id="session-classify",
    )
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=text)],
    )
    response_text = ""
    async for event in runner.run_async(
        user_id="api_user",
        session_id="session-classify",
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.strip("`").removeprefix("json").strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Agent returned invalid JSON: {response_text}")

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Classifier"], summary="Health check")
async def health():
    """Returns ok if the service is running."""
    return {"status": "ok", "agent": root_agent.name}


@app.post("/classify", tags=["Classifier"], summary="Classify input text", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    Classifies input text by sentiment and intent.
    - **sentiment**: positive | negative | neutral | mixed
    - **intent**: dynamically inferred (complaint, phishing, scam, feedback...)
    - **confidence**: 0.0 – 1.0
    - **reasoning**: one sentence explanation
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="'text' field must not be empty.")
    return await run_classifier(request.text)