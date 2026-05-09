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

## setion2
## Decision 3 — Structured Output Preprocessing Strategy

Date: 2026-04-XX
Phase: 2 — Structured Output

### Decision

Implement a hybrid preprocessing strategy:

* detect and log markdown fence wrapping as an instruction-compliance failure
* preserve the original raw output unchanged
* strip fences only in a secondary preprocessing step before JSON parsing
* continue structural validation on the cleaned output

Fence wrapping will therefore be treated as:

* a measurable instruction violation
* but not an unrecoverable structural failure

The validator will separately track:

* raw instruction compliance
* recoverable structural validity

---

### Evidence

During Phase 2 testing, markdown fence wrapping occurred in nearly all runs despite explicit prompt instructions:

* “Return ONLY valid JSON”
* “No markdown”
* “Do not include ```json fences”

At the same time:

* the underlying JSON content was structurally valid after cleanup
* no meaningful syntax or schema failures were observed

This revealed that:

* the model could follow structural requirements
* while simultaneously ignoring formatting instructions

The experiment therefore exposed two distinct behaviors:

1. instruction noncompliance
2. structural corruption

These behaviors should not be collapsed into the same failure category.

---

### Reasoning

Treating fence wrapping as a fatal syntax failure would artificially reduce measured structural reliability because the underlying JSON remained recoverable.

However, silently stripping fences without logging them would hide an important model behavior:

* persistent instruction noncompliance

The chosen strategy preserves both signals:

* operational usability
* experimental observability

This allows the system to answer questions such as:

* “Can the output be recovered safely?”
* “Did the model actually follow formatting instructions?”

This separation is important because:

* downstream systems may tolerate recoverable formatting noise
* but benchmark evaluation still needs visibility into compliance failures

The decision also keeps the experiment aligned with its stated Phase 2 goal:

> measuring structural reliability separately from semantic quality and instruction adherence.

---

### What This Decision Does NOT Answer

This decision does not determine:

* whether fence wrapping should count as a production failure
* whether recoverable preprocessing hides deeper instruction-following weaknesses
* how often fence wrapping occurs under different models or prompts
* whether preprocessing should extend to other recoverable artifacts
  (extra prose, trailing commas, malformed escaping, partial JSON, etc.)

It also does not answer:

* whether recoverable outputs should be included in headline “valid JSON” metrics

That remains an unresolved evaluation-policy question.

---

### When To Revisit

This decision should be revisited if:

* fence wrapping frequency changes significantly under different models
* preprocessing begins masking more serious structural failures
* retry behavior becomes sensitive to preprocessing logic
* downstream systems require strict raw-output compliance
* schema complexity increases and cleanup becomes ambiguous or unsafe
* Phase 3 introduces semantic correctness evaluation or production execution pipelines

The strategy should also be reconsidered if:

* recoverable preprocessing starts inflating benchmark metrics in misleading ways
* or if instruction compliance becomes a primary research objective rather than a secondary observation.

Decision 4 — Phase 2 Scope Limitation
Date: 2026-04-XX Phase: 2 — Structured Output
Decision
Phase 2 will be interpreted as a baseline structured generation reliability study under low-complexity conditions, not as a comprehensive robustness evaluation.
The experiment demonstrated that:

* gemma2:2b can reliably generate short structured JSON outputs for simple extraction tasks under strongly constrained prompting
The experiment did NOT demonstrate:

* robustness under complex schemas
* realistic failure distributions
* retry recovery effectiveness
* temperature-induced degradation boundaries
* semantic correctness reliability
Therefore, conclusions from Phase 2 will be limited strictly to:
baseline structural competence under controlled conditions.
Evidence
Observed results:

* 100% structurally valid outputs across all temperatures
* 0% recovery rate because retries were never triggered
* empty failure mode distribution
* no measurable syntax, missing-field, or wrong-type failures
At the same time:

* markdown fence wrapping occurred consistently
* indicating instruction noncompliance without structural corruption
The lack of observable failures prevented meaningful evaluation of:

* failure distributions
* retry behavior
* degradation patterns
* temperature sensitivity
Reasoning
The experiment encountered a ceiling effect.
A ceiling effect occurs when:

* task difficulty is too low relative to model capability
* causing performance metrics to saturate near 100%
When this happens:

* meaningful variance disappears
* failure mechanisms cannot be observed
* hypotheses about degradation become untestable
In this case:

* the schema was small
* outputs were short
* prompts were highly constrained
* task ambiguity remained limited
As a result, the benchmark primarily measured:
whether the model could succeed under favorable conditions
rather than:
how the system behaves under stress or instability.
This limits the strength of the conclusions because:

* absence of failures is not evidence that failures are impossible
* it only shows they did not emerge under current experimental pressure
A structurally easy benchmark can therefore produce:

* operational confidence while still failing to reveal:
* robustness boundaries
* hidden instability
* failure recovery behavior
What This Decision Does NOT Answer
This decision does not determine:

* at what schema complexity failures begin to emerge
* whether higher temperatures destabilize larger outputs
* whether retries are effective under realistic failure conditions
* whether semantic correctness degrades before structural validity
* how smaller or weaker models would behave under the same benchmark
* whether nested schemas would expose instability
* whether longer outputs increase schema drift probability
It also does not answer:

* whether the system is production-ready
* whether structural validity correlates with downstream correctness
When To Revisit
This decision should be revisited when:

* schema complexity increases
* nested objects or arrays are introduced
* prompt constraints are weakened
* semantic validation is added
* adversarial or ambiguous tasks are tested
* retries begin occurring naturally
* measurable failure distributions emerge
* larger output lengths are evaluated
* additional models are benchmarked comparatively
The scope limitation should also be reconsidered if:

* future experiments continue producing ceiling effects
* because that may indicate the benchmark design itself is insufficiently challenging rather than the model being universally robust.
