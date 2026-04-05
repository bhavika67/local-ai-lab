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

| Metric              | gemma2:2b | phi3:mini | Winner    |
|---------------------|-----------|-----------|-----------|
| Cold Start TTFT     | 2.417s    | 22.704s   | gemma2:2b |
| Warm Avg TTFT       | 2.406s    | 5.560s    | gemma2:2b |
| Warm Avg Latency    | 9.198s    | 21.042s   | gemma2:2b |
| Warm Avg TPS        | 8.58      | 5.37      | gemma2:2b |
| Thermal Stability   | Stable    | Unstable  | gemma2:2b |

Thermal evidence: phi3 TTFT spiked to 8.96s on run 4
after sustained inference. gemma showed no equivalent
spike across all 5 runs.

### Reasoning
In an edge deployment where the user is waiting for
a response and internet is not guaranteed, consistency
and speed matter more than the potential quality
advantages of a larger model. gemma2:2b wins on every
performance metric tested on this hardware.

### What This Decision Does NOT Answer
- Whether gemma2:2b output quality is good enough
  for real use cases
- How both models perform on longer or more complex prompts
- How performance changes under concurrent requests
- Whether the quality gap between models matters
  for specific task types
- Whether these results hold under sustained load
  over 30+ minutes

### When To Revisit
Phase 3 — after quality measurements across 30-50
standardized test prompts. If phi3 shows significantly
better quality on reasoning or structured output tasks,
this decision must be re-evaluated against the
performance tradeoff.

---