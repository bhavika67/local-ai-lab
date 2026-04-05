from fastapi import FastAPI
from pydantic import BaseModel
from benchmark import benchmark_model
import requests
import time
import json

app = FastAPI()


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


@app.post("/generate", response_model=BenchmarkResponse)
def generate(request: PromptRequest):
    result = benchmark_model(request.model, request.prompt)
    return BenchmarkResponse(**result)