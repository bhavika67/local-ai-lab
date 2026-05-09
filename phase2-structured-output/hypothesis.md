# Phase 2 - Structured Output Hypothesis
Date: 2026-04-XX
Device: Dell Inspiron 15 3520 | i5-1235U | 24GB RAM | No GPU

---

## What This Phase Is Testing

This phase tests whether small local LLMs can reliably generate
machine-consumable structured output under realistic conditions.

The question is not whether the model "understands JSON."
The question is: how often does probabilistic token generation
satisfy deterministic schema constraints — and what variables
control that rate?

Specifically, this phase measures how decoding parameters,
prompt design, and retry mechanisms affect schema validity,
failure distribution, and recovery behavior.

---

## Pre-Experiment Estimates

Committed before any code runs. These exist to be proven wrong.

| Condition                        | Expected Rate  |
|----------------------------------|----------------|
| Valid JSON at temperature 0.1    | 85 – 95%       |
| Valid JSON at temperature 0.7    | 55 – 75%       |
| Retry recovery of first failures | 40 – 70%       |

Reasoning:
- Low temperature stabilizes structural token selection.
  High-probability tokens dominate, maintaining syntax.
- At 0.7, lower-probability tokens gain real sampling weight.
  Structural tokens compete with continuations, explanations,
  and malformed punctuation.
- Retry success is high because most first-pass failures
  are prompt-repairable formatting errors, not capability
  limits. The model sees both the task and its own failure
  on the second attempt.

---

## Hypothesis 1 — Failure Mode Distribution

Prediction:

| Failure Mode    | Expected Share |
|-----------------|----------------|
| Missing fields  | ~55%           |
| Invalid syntax  | ~25%           |
| Wrong types     | ~20%           |

Reasoning:
Missing fields will dominate because small models optimize
for semantic completeness, not schema completeness. When a
response feels linguistically finished, generation stops —
regardless of whether all required fields were emitted.

Invalid syntax occurs less often because JSON structural
patterns are heavily represented in training data. Braces,
commas, and quotes are high-probability continuations at
low temperature.

Wrong types occur least but still appear. The model has no
internal type system. "true" and true are different token
sequences with different probabilities — not boolean versus
string representations of the same value.

Falsified if:
- Missing fields are NOT dominant → the model is failing
  at structural continuity, not schema completion.
  Action: investigate prompt structure and field ordering.
- Invalid syntax exceeds 50% of failures → sampling
  instability or prompt ambiguity is overwhelming learned
  JSON patterns.
  Action: fix the prompt before touching temperature.

Minimum sample size: 300–500 attempts per configuration.
Below 100 samples, you are observing anecdotes.
Above 300, you begin observing distributions.

---

## Hypothesis 2 — Temperature vs Schema Validity

Prediction: valid JSON rate decreases as temperature increases.

| Temperature Range | Expected Behavior                        |
|-------------------|------------------------------------------|
| 0.0 → 0.3         | Validity stable, syntax consistent       |
| 0.4 → 0.7         | Schema errors increase noticeably        |
| 0.8 → 1.0         | Structured output becomes unstable       |

Controlled variables — held constant across all runs:
- Prompt: same fixed prompt
- Schema: tested separately at simple / nested / multi-field
- Model, context length, system prompt, max tokens: fixed
- Retry logic: disabled during temperature testing
- Hardware and input dataset: fixed

Reasoning:
Temperature rescales the token probability distribution
before sampling. Low temperature sharpens the distribution —
structural tokens dominate. High temperature flattens it —
lower-probability tokens gain real sampling weight, increasing
the chance of malformed punctuation, duplicate keys,
mid-JSON explanations, or incomplete structures.

JSON validity depends on deterministic repetition of
structural tokens. Higher temperature directly attacks that.

Falsified if:
- Valid JSON at 0.7 exceeds 85% → the model is more
  structurally robust than predicted.
  Action: push temperature higher before treating
  low temperature as a hard requirement.
- Valid JSON at 0.1 falls below 70% → failures are caused
  by prompt design or capability limits, not sampling.
  Action: fix the prompt. Temperature is not the problem.

---

## Hypothesis 3 — Retry Behavior

Prediction: retry will recover 40–70% of first-pass failures,
especially for formatting and missing-field errors.

What a retry success actually measures:
A retry success does not mean the model became more capable.
It means the system provided better constraints. The retry
exposes the failure, lengthens the prompt, and narrows the
valid output space. The model now sees both the original task
and the consequence of its first attempt.

Retry measures prompt robustness and recoverability —
not model intelligence.

What a retry failure actually means:
The current combination of model size, prompt design, schema
complexity, and decoding parameters exceeds the model's
reliability boundary. The system failed to constrain
generation into a valid format even with explicit feedback.
This is a system design failure, not a model failure.

Falsified if:
- Retry recovers less than 25% of failures → failures are
  semantic or capability-related, not prompt-repairable.
  Action: simplify the schema or accept that this model
  cannot reliably handle this task type.
- Retry success rate equals first-pass rate → corrective
  feedback provides no useful constraint signal.
  Action: redesign the retry prompt. Showing the error
  is not enough — the feedback must be specific.

---

## Concepts To Understand Before Running Any Code

### Why Small Models Fail At Structured Output
Small LLMs predict tokens sequentially from learned
statistical patterns. JSON generation works because the
model has seen many JSON-like examples — not because it
understands formal grammars. Longer or nested schemas
require tracking long-range structural dependencies,
which smaller models handle poorly.

Structured output failure is a probabilistic sampling
problem, not a "bad model" problem.

### What Temperature Actually Does
Temperature is not a creativity dial. It rescales the
token probability distribution before sampling. Low
temperature sharpens the distribution — high-probability
tokens dominate. High temperature flattens it — allowing
lower-probability tokens to appear more often.

In structured generation, low temperature wins because
valid JSON depends on predictable, high-probability
structural continuations.

### What Retry Actually Tests
Retry tests whether additional constraints can guide the
model back into the valid output space. It measures prompt
repairability and validator usefulness — not intelligence.

A retry system compensates for nondeterministic generation
through iterative constraint refinement. It is a system
design tool, not a model evaluation tool.

---

## Engineering Notes

### Why Small Error Rates Compound
A 95% valid JSON rate sounds reliable. In a multi-step
pipeline it is not:

  95% JSON validity
  × 95% field correctness
  × 95% type correctness
  = ~86% end-to-end reliability

1 in 7 requests fails silently. That is why evaluation
at scale matters — small error rates multiply fast.

### Why Controlled Experiments Are Non-Negotiable
Changing multiple variables simultaneously makes results
uninterpretable. A fair evaluation changes exactly one
variable at a time. Temperature effects measured against
different prompts, schemas, or retry strategies are not
temperature effects — they are noise with labels.

---

## What I Don't Know Yet

1. At what schema complexity does validity sharply collapse
   for gemma2:2b specifically?

2. Whether failure modes are consistent across runs or
   whether the same prompt randomly succeeds and fails —
   and what that variance means for production reliability.

3. How much validity improvement comes from prompt
   engineering alone versus constrained decoding.

4. Whether retry loops plateau after 2 attempts or continue
   improving with additional corrective feedback.

5. Whether certain field ordering patterns statistically
   improve completion rates — does putting simple fields
   first help the model build structural momentum?

6. Whether LLM-as-judge validation introduces hidden bias
   during repair loops.

7. How strongly context length affects schema stability as
   conversation history grows.

8. Whether temperature effects on validity differ across
   failure modes — does syntax break before fields go
   missing, or simultaneously?

---

## When To Revisit
Phase 3 — when comparing structured output reliability
across multiple models. Every number measured here becomes
the baseline. If Phase 3 comparisons are made without
this baseline, model differences cannot be separated from
prompt or temperature differences.