# Local AI Lab — Edge Deployment Project

A structured benchmarking project evaluating small local language models
for edge deployment on consumer hardware. Built across three phases using
Ollama, FastAPI, and Python.

---

## The Question This Project Answers

Can small local language models reliably generate structured outputs,
and which model provides the best balance between quality, reliability,
and deployment efficiency for resource-constrained environments?

---

## Key Findings

**Finding 1 — Structural reliability was not the main differentiator.**
All three models achieved very high structured output validity. The largest
differences emerged from semantic correctness rather than JSON generation ability.

**Finding 2 — Evaluation logic can change conclusions.**
The original language metric produced near-zero accuracy for all models.
After fixing the scoring logic, language accuracy became near-perfect.
Benchmark design has as much impact as model capability.

**Finding 3 — qwen2.5:3b emerged as a serious challenger.**
The expectation was that gemma2:2b would clearly remain the strongest
deployment choice. Instead, qwen2.5:3b matched or exceeded gemma2:2b on
several semantic quality measures and showed superior robustness as
temperature increased.

---

## Final Deployment Recommendations

| Model       | Recommendation | Best For                                      |
|-------------|---------------|-----------------------------------------------|
| gemma2:2b   | Primary        | Edge deployment, latency-sensitive, resource-constrained |
| qwen2.5:3b  | Secondary      | Quality-focused, classification-heavy, temperature-robust |
| llama3.2:3b | Not recommended| No measured advantage in any category         |

---

## What Was Built

### Phase 1 — Baseline Model Evaluation
Benchmarked local models on inference speed, time to first token, tokens
per second, and thermal stability. Established gemma2:2b as the primary
deployment model. Built a FastAPI wrapper around Ollama for structured
request handling.

Key files:
- `benchmark.py` — core inference measurement
- `app.py` — FastAPI wrapper
- `phase1-benchmarking/` — hypothesis, observations, results

### Phase 2 — Structured Output Reliability Framework
Built a validation and benchmarking harness capable of detecting JSON
failures, schema violations, markdown fence wrapping, and retry recovery
behavior. Ran 220 structured generation experiments across 4 temperatures.

Key files:
- `phase2-structured-output/structured_generation.py` — validator and retry pipeline
- `phase2-structured-output/run_phase2_experiment.py` — experiment harness
- `phase2-structured-output/phase2_results.jsonl` — raw results

### Phase 3 — Comparative Model Benchmarking
Extended the benchmark to compare gemma2:2b, llama3.2:3b, and qwen2.5:3b
across 3 temperatures using semantic quality scoring, adversarial inputs,
toxicity detection, sarcasm detection, and confidence calibration.
Ran 324 experiments with ground-truth quality labels.

Key files:
- `phase3-model-comparison/run_phase3_experiment.py` — experiment harness
- `phase3-model-comparison/rescore.py` — rescoring with fixed language metric
- `phase3-model-comparison/quality_labels.json` — ground truth labels
- `phase3-model-comparison/phase3_results.jsonl` — raw results

---

## Hardware

All benchmarking was conducted on local development hardware with no GPU.

| Component | Details                          |
|-----------|----------------------------------|
| Device    | Dell Inspiron 15 3520            |
| CPU       | Intel i5-1235U (1.30 GHz base)   |
| RAM       | 24GB                             |
| GPU       | None — CPU inference only        |
| OS        | Windows                          |
| Runtime   | Ollama                           |
| Environment | Python virtual environment (.venv) |

All models were executed locally through Ollama under identical conditions.
Future benchmarks should use the same hardware configuration when comparing
results across project phases.

---

## Project Structure

```
local-ai-lab/
  app.py                          FastAPI wrapper
  benchmark.py                    Core inference measurement
  decission.md                    Decision log (all 7 decisions)
  README.md                       This file

  phase1-benchmarking/
    hypothesis.md
    observation.md

  phase2-structured-output/
    structured_generation.py      Validator and retry pipeline
    run_phase2_experiment.py      Experiment harness
    inputs.json                   55 test inputs
    phase2_results.jsonl          Raw results

  phase3-model-comparison/
    structured_generation.py      Validator (Phase 3 version)
    run_phase3_experiment.py      Experiment harness
    rescore.py                    Rescoring with language fix
    inputs_phase3.json            36 test inputs
    quality_labels.json           Ground truth labels
    phase3_results.jsonl          Raw results
```

---

## Setup

### Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- Required models pulled

### Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install fastapi uvicorn requests
```

### Pull models

```bash
ollama pull gemma2:2b
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
```

---

## Running Each Phase

### Phase 1 — Inference Benchmark

```bash
python benchmark.py
```

Runs 5 benchmarks each for phi3:mini and gemma2:2b.
Results printed to terminal.

### Phase 1 — FastAPI Server

```bash
uvicorn app:app --reload
```

Exposes `/generate` and `/analyze` endpoints on port 8000.

### Phase 2 — Structured Output Experiment

```bash
cd phase2-structured-output
python run_phase2_experiment.py
```

Runs 220 experiments across 55 inputs and 4 temperatures.
Results written to `phase2_results.jsonl`.

### Phase 3 — Comparative Model Benchmark

```bash
cd phase3-model-comparison
python run_phase3_experiment.py
```

Runs 324 experiments across 3 models, 36 inputs, and 3 temperatures.
Results written to `phase3_results.jsonl`.

### Phase 3 — Rescore with Language Fix

```bash
cd phase3-model-comparison
python rescore.py
```

Rescores existing results with corrected language normalization.
Does not rerun model calls.

---

## Documentation

Every design decision in this project is logged in `decission.md` with:
- What was decided
- What evidence it was based on
- What the decision does not answer
- When it should be revisited

Each phase folder contains a `hypothesis.md` written before running
experiments and an `observation.md` written after.