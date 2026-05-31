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

| Metric           | Value                           |
|------------------|---------------------------------|
| TTFT             | 6.589s                          |
| Total Latency    | 11.332s                         |
| Tokens/Second    | 2.82                            |
| Token Count      | 32                              |
| HTTP Status      | 200                             |
| Response Quality | Correct, one sentence, accurate |

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

---

## Decision 3 — Structured Output Preprocessing Strategy
Phase: 2 — Structured Output

### Decision
Implement a hybrid preprocessing strategy:

- Detect and log markdown fence wrapping as an
  instruction-compliance failure
- Preserve the original raw output unchanged in logs
- Strip fences only in a secondary preprocessing step
  before JSON parsing
- Continue structural validation on the cleaned output

Fence wrapping will be treated as:
- A measurable instruction violation
- But not an unrecoverable structural failure

The validator separately tracks:
- Raw instruction compliance (fence_detected)
- Recoverable structural validity (is_valid)

### Evidence
During Phase 2 testing, markdown fence wrapping occurred
on nearly every run despite explicit prompt instructions:

- "Return ONLY valid JSON"
- "No markdown"
- "Do not include ```json fences"

At the same time:
- The underlying JSON content was structurally valid after cleanup
- No meaningful syntax or schema failures were observed

This revealed two distinct behaviors:
1. Instruction noncompliance — formatting instructions ignored
2. Structural correctness — JSON content remained valid

These behaviors must not be collapsed into the same failure
category. Collapsing them would either artificially inflate
failure rates or silently hide compliance failures.

### Reasoning
Treating fence wrapping as a fatal syntax failure would
artificially reduce measured structural reliability because
the underlying JSON remained recoverable.

Silently stripping fences without logging them would hide
a persistent model behavior that matters in production:
the model consistently ignores explicit formatting instructions.

The hybrid strategy preserves both signals:
- Operational usability: outputs can be recovered and used
- Experimental observability: instruction failures are logged

This separation allows the system to answer two distinct
questions independently:
- "Can the output be recovered safely?" → is_valid
- "Did the model follow formatting instructions?" → fence_detected

### What This Decision Does NOT Answer
- Whether fence wrapping should count as a production failure
- Whether recoverable preprocessing hides deeper weaknesses
- How fence wrapping frequency compares across different models
- Whether preprocessing should extend to other recoverable
  artifacts such as trailing commas, extra prose, or partial JSON
- Whether recoverable outputs should be included in headline
  valid JSON metrics — this remains an open evaluation policy

### When To Revisit
- If fence wrapping frequency changes significantly across models
- If preprocessing begins masking more serious structural failures
- If retry behavior becomes sensitive to preprocessing logic
- If downstream systems require strict raw-output compliance
- If schema complexity increases and cleanup becomes ambiguous
- If Phase 3 introduces semantic correctness evaluation or
  production execution pipelines

---

## Decision 4 — Phase 2 Scope Limitation
Phase: 2 — Structured Output

### Decision
Phase 2 results will be interpreted as a baseline structured
generation reliability study under low-complexity conditions —
not as a comprehensive robustness evaluation.

The experiment demonstrated:
- gemma2:2b can reliably generate short structured JSON outputs
  for simple extraction tasks under strongly constrained prompting

The experiment did NOT demonstrate:
- Robustness under complex or nested schemas
- Realistic failure distributions
- Retry recovery effectiveness
- Temperature-induced degradation boundaries
- Semantic correctness reliability

Conclusions from Phase 2 are limited strictly to:
baseline structural competence under controlled conditions.

### Evidence

| Metric                | Observed Value           |
|-----------------------|--------------------------|
| First-pass valid rate | 100% at all temperatures |
| Recovery rate         | 0% (no retries needed)   |
| Syntax failures       | 0                        |
| Missing field failures| 0                        |
| Wrong type failures   | 0                        |
| Fence wrapping rate   | ~100% of runs            |

The lack of observable structural failures prevented
meaningful evaluation of:
- Failure mode distributions
- Retry behavior
- Degradation patterns under temperature variation
- Robustness boundaries

### Reasoning
The experiment encountered a ceiling effect.

A ceiling effect occurs when task difficulty is too low
relative to model capability, causing performance metrics
to saturate near 100%. When this happens:
- Meaningful variance disappears
- Failure mechanisms cannot be observed
- Hypotheses about degradation become untestable

Contributing factors in this experiment:
- Schema was small (3 fields)
- Outputs were short (~27 tokens average)
- Prompts were highly constrained
- Task ambiguity remained limited

The benchmark therefore measured whether the model could
succeed under favorable conditions — not how the system
behaves under stress.

Critical distinction:
Absence of failures is not evidence that failures are
impossible. It only means they did not emerge under the
current experimental pressure.

### What This Decision Does NOT Answer
- At what schema complexity failures begin to emerge
- Whether higher temperatures destabilize larger outputs
- Whether retries are effective under realistic failure conditions
- Whether semantic correctness degrades before structural validity
- How smaller or weaker models would behave under the same benchmark
- Whether nested schemas would expose instability
- Whether the system is production-ready

### When To Revisit
- When schema complexity increases
- When nested objects or arrays are introduced
- When prompt constraints are deliberately weakened
- When semantic validation is added
- When adversarial or ambiguous tasks are tested
- When retries begin occurring naturally
- When additional models are benchmarked comparatively

If future experiments continue producing ceiling effects,
the benchmark design itself must be questioned — not just
the model behavior.

---

## Session 2 End
Completed Phase 2 in full.
Stopping point: about to begin Phase 3 —
comparative model benchmarking.

Open questions to answer at start of next session:
1. Which two additional models will be compared against gemma2:2b?
2. How will output quality be measured — what is the rubric?
3. How will the Phase 3 benchmark be designed to produce
   failures rather than just measure success rates?

## Decision 5 — Primary Model Recommendation Confirmed

Phase: 3 — Comparative Model Benchmarking

### Decision

gemma2:2b remains the primary deployment model for edge deployment with one important qualification added.

Phase 3 did not overturn the original deployment recommendation established in Phase 1. gemma2:2b continues to provide the strongest balance between semantic quality, structural reliability, deployment efficiency, and hardware requirements.

However, Phase 3 demonstrated that qwen2.5:3b is a credible challenger rather than merely a comparison baseline. Future deployment decisions should therefore consider both models rather than treating gemma2:2b as the uncontested default.

### Evidence

Structural reliability remained extremely strong:

| Model       | First-Pass Valid Range |
| ----------- | ---------------------- |
| gemma2:2b   | 97–100%                |
| llama3.2:3b | 94–97%                 |
| qwen2.5:3b  | 100%                   |

At temperature 0.1:

| Model       | Pass Rate | Avg Score |
| ----------- | --------- | --------- |
| gemma2:2b   | 90.91%    | 0.973     |
| qwen2.5:3b  | 90.91%    | 0.945     |
| llama3.2:3b | 31.82%    | 0.733     |

Additional findings:

* Highest average quality score in the benchmark
* Excellent sentiment accuracy
* Excellent confidence calibration
* Near-perfect structural reliability
* Smallest deployment footprint among evaluated models
* Successfully defended the original deployment recommendation against two competing models

### What This Decision Does NOT Answer

* Whether gemma2:2b remains optimal for reasoning-intensive tasks
* Whether gemma2:2b remains optimal for code generation tasks
* Whether qwen2.5:3b's semantic advantages justify its larger deployment footprint in some environments
* Whether gemma2:2b would remain the preferred model under substantially larger schemas
* Whether future local models will outperform both gemma2:2b and qwen2.5:3b

### When To Revisit

* If a future benchmark introduces nested or significantly larger schemas
* If deployment hardware changes substantially
* If a new local model demonstrates a better efficiency-to-quality ratio
* If qwen2.5:3b maintains a quality advantage across additional benchmark phases
* If future benchmarks prioritize reasoning, coding, or long-context tasks

---
