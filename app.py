from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError
from benchmark import benchmark_model
import json
import re
from typing import Literal

app = FastAPI()


# ---- Schemas ----
class PromptRequest(BaseModel):
    model: str
    prompt: str


class BenchmarkResponse(BaseModel):
    model: str
    response: str
    ttft_seconds: float
    total_latency_seconds: float
    tokens_per_second: float
    token_count: int


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)


# ---- Helpers ----
def extract_and_validate(raw_response: str) -> SentimentResponse:
    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    data = json.loads(match.group())
    return SentimentResponse(**data)


# ---- Routes ----
@app.post("/generate", response_model=BenchmarkResponse)
def generate(request: PromptRequest):
    result = benchmark_model(request.model, request.prompt)
    return BenchmarkResponse(**result)


@app.post("/analyze", response_model=SentimentResponse)
def analyze(request: SentimentRequest):
    prompt = f"""
    Analyze the sentiment of the following text.
    Text: "{request.text}"
    Return a JSON object with sentiment and confidence.
    "sentiment" can only be "positive", "negative", or "neutral".
    "confidence" must be a float between 0.0 and 1.0.
    Output ONLY valid JSON like this:
    {{"sentiment": "positive", "confidence": 0.92}}
    """

    result = benchmark_model("gemma2:2b", prompt)
    raw_response = result["response"]

    try:
        return extract_and_validate(raw_response)

    except (json.JSONDecodeError, ValidationError, ValueError):
        retry_prompt = f"""
        Your previous response was invalid.
        Text: "{request.text}"
        Previous response:
        {raw_response}
        Fix the errors:
        - Must be valid JSON
        - "sentiment" must be "positive", "negative", or "neutral"
        - "confidence" must be a float between 0.0 and 1.0
        Return ONLY valid JSON like:
        {{"sentiment": "positive", "confidence": 0.92}}
        """

        retry_result = benchmark_model("gemma2:2b", retry_prompt)
        retry_raw_response = retry_result["response"]

        try:
            return extract_and_validate(retry_raw_response)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Model failed after retry",
                    "first_response": raw_response,
                    "retry_response": retry_raw_response,
                    "reason": str(e)
                }
            )