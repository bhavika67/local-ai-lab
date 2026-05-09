# Phase 2 - Structured Output Observations

Date: 2026-04-XX
Device: Dell Inspiron 15 3520 | i5-1235U | 24GB RAM | No GPU
Model: gemma2:2b
Schema: sentiment (str), confidence (float), is_toxic (bool)
Temperatures tested: 0.1, 0.4, 0.7, 1.0
Total runs: 220 (55 inputs × 4 temperatures)

---

# Part 1 - Raw Results

Across all 220 runs, the model produced structurally valid JSON outputs after preprocessing. Reported valid JSON rate was 100% at every tested temperature level, including 0.7 and 1.0, where the original hypothesis predicted substantial degradation.

Observed recovery rate was 0% across all temperatures because no retries were triggered. Attempt 1 succeeded on every run according to the validator.

Failure mode distribution was empty:

* no syntax failures
* no missing fields
* no wrong types
* no retry-triggering outputs

However, an important hidden behavior emerged during inspection of raw outputs: markdown fence wrapping occurred consistently. The model frequently returned responses inside ```json code fences despite explicit prompt instructions forbidding them.

This introduced a distinction between:

* structural validity after cleanup
* strict instruction compliance

The validator therefore measured recoverable structural correctness rather than raw instruction obedience.

---

# Part 2 - Hypothesis Evaluation

## Hypothesis 1 — Failure Mode Distribution

Original prediction:

* missing fields would dominate failures (~55%)
* syntax failures would occur less frequently
* wrong types would occur occasionally

Observed result:

* no measurable failures occurred

Conclusion:
The hypothesis was not supported by the collected data. However, this does not necessarily prove the reasoning mechanism was incorrect. Instead, the experiment likely failed to generate enough difficulty to expose the predicted failure modes.

Possible causes:

* schema complexity was too low
* prompt constraints were too strong
* output length was too short
* the model operated within a stable reliability range for this task

The experiment therefore did not meaningfully test failure distributions because almost no observable failures were produced.

---

## Hypothesis 2 — Temperature vs Schema Validity

Original prediction:

* valid JSON rate would decrease as temperature increased
* temperature 0.7+ would introduce noticeable schema instability

Observed result:

* 100% valid JSON rate across all tested temperatures

Conclusion:
The hypothesis was falsified under current experimental conditions.

However, this does not necessarily imply:

> temperature has no effect on structured generation.

Instead, the task likely exhibited a ceiling effect where:

* the schema was sufficiently simple
* prompt constraints sufficiently explicit
* model capability sufficiently strong

that temperature variation alone could not destabilize generation.

This means the benchmark lacked enough structural pressure to reveal probabilistic degradation patterns.

The experiment therefore measured:

> stable structured generation under low-complexity constraints

rather than:

> failure dynamics under probabilistic stress.

---

## Hypothesis 3 — Retry Behavior

Original prediction:

* retries would recover 40–70% of failures

Observed result:

* recovery rate = 0%

Interpretation:
This was operationally positive but experimentally inconclusive.

Operationally:

* the system succeeded on first-pass generation consistently
* retries were unnecessary

Experimentally:

* the retry mechanism was never meaningfully exercised
* no evidence was collected regarding retry effectiveness

Therefore:

* the hypothesis was not truly evaluated
* retry recovery behavior remains unknown

The result does not mean:

> retries are ineffective.

It means:

> the benchmark produced no retry-triggering conditions.

This distinction is critical.

---

# Part 3 - Surprise Findings

## Surprise 1 — Fence Wrapping (100% of runs)

Despite explicit instructions:

* “Return ONLY valid JSON”
* “No markdown”
* “Do not include ```json fences”

the model consistently wrapped outputs in markdown code fences.

This revealed an important distinction between:

* structural validity
* instruction compliance

The model successfully produced parseable JSON content while simultaneously violating formatting instructions.

This suggests that:

* markdown-wrapped JSON is deeply reinforced in training distributions
* prompt instructions alone may not fully suppress learned formatting patterns

It also exposed an important validator design decision:
Should recoverable fence wrapping count as:

* valid output?
* instruction failure?
* syntax failure?
* recoverable preprocessing?

The experiment therefore uncovered a new measurable failure category:

> instruction noncompliance without structural corruption.

---

## Surprise 2 — Ceiling Effect

The benchmark produced almost no observable structural failures across 220 runs.

This was unexpected because the original hypothesis assumed:

* higher temperatures
* noisy inputs
* ambiguous text
* toxic content

would destabilize schema adherence.

Instead, the experiment encountered a ceiling effect:
the task was too easy relative to the model’s capabilities under the given prompt constraints.

This demonstrates an important benchmarking lesson:
A benchmark that produces no failures may still be scientifically weak because it cannot reveal:

* degradation boundaries
* failure distributions
* retry dynamics
* robustness characteristics

The experiment therefore validated baseline competence rather than stress behavior.

---

# Part 4 - What The Experiment Actually Measured

The experiment ultimately measured:

* whether gemma2:2b could reliably generate short structured JSON outputs under strongly constrained prompting conditions

It did NOT meaningfully measure:

* structural failure distributions
* retry recovery effectiveness
* temperature-induced instability
* semantic correctness
* robustness under complex schemas

The validator measured:

* syntax
* field presence
* type correctness

It did not measure:

* semantic quality
* sentiment correctness
* toxicity accuracy
* reasoning validity

Therefore, Phase 2 should be interpreted as:

> a baseline structured generation reliability study

not:

> a comprehensive robustness evaluation.

---

# Part 5 - What My Hypothesis Got Wrong

The original hypothesis overestimated:

* the destabilizing effect of temperature
* the frequency of structural failures
* the likelihood of retry-triggering outputs

The hypothesis implicitly assumed:

* small local models are fragile under structured generation

But the observed results suggest:

* strongly constrained prompts can dramatically stabilize simple schema generation
* simple extraction tasks may remain stable even at higher temperatures

Another mistake was assuming:

* retry behavior would naturally emerge during experimentation

In reality:

* retries depend entirely on the existence of failures
* no failures means no retry observations

The experiment also revealed an overlooked factor:

* instruction noncompliance can coexist with structurally valid outputs

This distinction was not captured in the original hypothesis design.

---

# Part 6 - Open Questions For Next Phase

1. At what schema complexity does structured validity begin to degrade?

2. Does temperature affect nested or multi-object schemas more strongly than flat schemas?

3. Would weaker prompts reveal stronger temperature sensitivity?

4. Does removing explicit JSON instructions expose larger structural failure rates?

5. How does model size affect structured reliability under identical prompts?

6. Can retry loops recover semantic failures as effectively as structural failures?

7. Should instruction noncompliance (markdown fences) be treated as a recoverable formatting issue or a true generation failure?

8. How should semantic correctness be evaluated separately from structural validity?

9. Would adversarial or intentionally confusing inputs produce measurable retry behavior?

10. Does increasing output length increase schema drift probability at higher temperatures?
