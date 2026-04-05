# Decision Log
# Local AI Lab — Edge Deployment Project
Started: 2026-04-05

---

## How To Use This File

Every decision in this project is logged here.
Each entry must include:
- What was decided
- What evidence it was based on
- What the decision does NOT answer
- When it can be revisited

A decision without evidence is a guess.
A decision without limits is overconfidence.

---

## Decision 1 — Primary Model Selection
Date: 2026-04-05
Phase: 1 — Inference Benchmarking

### Decision
Use gemma2:2b as the primary model for edge deployment.

### Evidence

| Metric            | gemma2:2b | phi3:mini | Winner    |
|-------------------|-----------|-----------|-----------|
| Cold Start TTFT   | 2.417s    | 22.704s   | gemma2:2b |
| Warm Avg TTFT     | 2.406s    | 5.560s    | gemma2:2b |
| Warm Avg Latency  | 9.198s    | 21.042s   | gemma2:2b |
| Warm Avg TPS      | 8.58      | 5.37      | gemma2:2b |
| Thermal Stability | Stable    | Unstable  | gemma2:2b |

Thermal evidence: phi3 TTFT spiked to 8.96s on run 4
after sustained inference. gemma showed no equivalent
spike across all 5 runs.

### Reasoning
In an edge deployment where the user is waiting for a
response and internet is not guaranteed, consistency and
speed matter more than the potential quality advantages
of a larger model. gemma2:2b wins on every performance
metric tested on this hardware.

### What This Decision Does NOT Answer
- Whether gemma2:2b output quality is good enough for real use cases
- How both models perform on longer or more complex prompts
- How performance changes under concurrent requests
- Whether the quality gap between models matters for specific task types
- Whether these results hold under sustained load over 30+ minutes

### When To Revisit
Phase 3 — after quality measurements across 30-50 standardized
test prompts. If phi3 shows significantly better quality on
reasoning or structured output tasks, this decision must be
re-evaluated against the performance tradeoff.

---

## Decision 2 — FastAPI Wrapper Architecture
Date: 2026-04-05
Phase: 1 — Infrastructure

### Decision
Wrap Ollama in a FastAPI layer rather than calling Ollama
directly from every client application.

### Reasoning
Ollama already exposes a raw API on port 11434. Adding FastAPI
on top creates a single point of control for the entire system.

Benefits:
- All request logging happens in one place
- Validation and retry logic added once, applies everywhere
- Authentication can be added without changing any client
- Response format is consistent regardless of model being called
- Future features added to FastAPI benefit all clients

### API Test Result
Prompt: "What is machine learning in one sentence?"
Model: gemma2:2b

| Metric               | Value  |
|----------------------|--------|
| TTFT                 | 6.589s |
| Total Latency        | 11.332s |
| Tokens/Second        | 2.82   |
| Token Count          | 32     |
| HTTP Status          | 200    |
| Response Quality     | Correct, one sentence, accurate |

Note on low TPS (2.82 vs benchmark avg 8.58):
Caused by model being unloaded from memory after a long
idle period during documentation work. Ollama unloads
inactive models automatically. First request after an
idle period always pays the cold start penalty.

Production implication: For edge deployment with
unpredictable usage patterns, cold start penalty will
appear regularly. Consider keeping the model warm with
a periodic heartbeat request if consistent low latency
is required.

### Lessons Learned During Implementation

#### Lesson 1 — The __main__ Guard
benchmark.py must use `if __name__ == "__main__"` to
protect benchmark code from running on import.

Without this guard, importing benchmark_model into app.py
triggered the entire 10-run benchmark before the FastAPI
server could start. This is a standard Python pattern that
must always be used when a file serves dual purpose — as
both a runnable script and an importable module.

#### Lesson 2 — Ollama Model Caching
Ollama keeps recently used models loaded in memory after
a run completes. This means running a benchmark immediately
after a previous run gives artificially fast cold start numbers.
True cold start requires restarting Ollama first.

Command to restart Ollama on Windows:
  net stop ollama
  net start ollama

Always restart Ollama before measuring cold start.
Otherwise cold start numbers are not trustworthy.

#### Lesson 3 — Return Dictionary Must Match Response Schema
When benchmark_model is called from FastAPI, its return
dictionary must contain every field that BenchmarkResponse
expects. Missing fields cause a runtime crash, not a startup
error. Always verify that function return values match the
Pydantic model schema exactly.

### What This Decision Does NOT Answer
- How to handle authentication for multi-user scenarios
- How to handle concurrent requests safely
- Whether FastAPI overhead affects latency meaningfully
- How to add streaming responses through the API layer

### When To Revisit
Phase 2 — when adding structured output validation and retry
logic. The FastAPI layer is where these features will live.

---
## Session 1 End — 2026-04-05
Completed Phase 1 in full.
Stopping point: about to begin Phase 2 — 
structured output and JSON validation.

Open question to answer at start of next session:
If gemma2:2b is asked to return JSON, what are
the three ways it can fail?