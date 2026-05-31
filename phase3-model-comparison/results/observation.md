# Phase 3 - Comparative Model Benchmarking Observations

**Date:** 2026-05-31
**Models:** gemma2:2b, llama3.2:3b, qwen2.5:3b
**Inputs:** 36 (22 scoreable, 14 unscoreable)
**Temperatures:** 0.1, 0.7, 1.0
**Total Runs:** 324

---

# Part 1 - Raw Results

| Model       | Temp | First-pass Valid | Pass Rate | Avg Score |
| ----------- | ---- | ---------------- | --------- | --------- |
| gemma2:2b   | 0.1  | 100.00%          | 90.91%    | 0.973     |
| gemma2:2b   | 0.7  | 100.00%          | 68.18%    | 0.909     |
| gemma2:2b   | 1.0  | 97.22%           | 59.09%    | 0.914     |
| llama3.2:3b | 0.1  | 94.44%           | 31.82%    | 0.733     |
| llama3.2:3b | 0.7  | 97.22%           | 22.73%    | 0.657     |
| llama3.2:3b | 1.0  | 94.44%           | 18.18%    | 0.695     |
| qwen2.5:3b  | 0.1  | 100.00%          | 90.91%    | 0.945     |
| qwen2.5:3b  | 0.7  | 100.00%          | 81.82%    | 0.909     |
| qwen2.5:3b  | 1.0  | 100.00%          | 72.73%    | 0.882     |

## Immediate Observations

1. Structural validity was extremely high across all models.
2. gemma2:2b and qwen2.5:3b dramatically outperformed llama3.2:3b.
3. qwen2.5:3b showed the strongest robustness to increasing temperature.
4. gemma2:2b achieved the highest average score at temperature 0.1.
5. llama3.2:3b never exceeded a 31.82% pass rate.
6. After rescoring, the language metric no longer materially affected rankings.

---

# Part 2 - Hypothesis Evaluation

## Hypothesis 1 — Structural Reliability

### Prediction

All models would show some degradation in structured generation reliability as schema complexity increased.

### Result

Partially supported.

Structural reliability remained extremely high across all three models.

| Model       | First-pass Valid Range |
| ----------- | ---------------------- |
| gemma2:2b   | 97–100%                |
| llama3.2:3b | 94–97%                 |
| qwen2.5:3b  | 100%                   |

The larger schema did not create significant structural failures.

Most failures occurred at the semantic level rather than the structural level.

### Conclusion

Phase 3 became primarily a semantic benchmark rather than a structural generation benchmark.

---

## Hypothesis 2 — Failure Mode Distribution

### Prediction

Models would primarily fail through malformed JSON, missing fields, and retry-triggering errors.

### Result

Not supported.

The dominant failure modes were:

* invalid_sentiment
* confidence_out_of_range
* sarcasm_mismatch

Structural failures were rare.

### Conclusion

Model differences emerged from semantic interpretation rather than JSON generation.

---

## Hypothesis 3 — Quality on Unambiguous Inputs

### Prediction

Clear positive, negative, neutral, and toxic inputs would separate model performance.

### Result

Strongly supported.

At temperature 0.1:

| Model       | Pass Rate |
| ----------- | --------- |
| gemma2:2b   | 90.91%    |
| qwen2.5:3b  | 90.91%    |
| llama3.2:3b | 31.82%    |

The benchmark successfully differentiated model quality.

### Conclusion

The scoreable dataset produced meaningful separation between models.

---

## Hypothesis 4 — Performance vs Quality Tradeoff

### Prediction

The deployment-efficient model would sacrifice some semantic quality.

### Result

Partially contradicted.

gemma2:2b remained highly competitive despite being the smallest model tested.

qwen2.5:3b achieved superior robustness while maintaining comparable quality.

llama3.2:3b failed to demonstrate a quality advantage despite larger size.

### Conclusion

Model size alone was not predictive of benchmark performance.

---

# Part 3 - Surprise Findings

## Surprise 1 — Language Metric Was Broken

The original scoring logic treated language values too strictly.

Examples such as:

* english
* English
* EN

were evaluated differently despite representing the same answer.

After normalization, language accuracy increased dramatically across all models.

### Impact

The original language findings were invalid.

The benchmark evaluation code, rather than the models, caused the observed failures.

### Lesson

Evaluation logic should be audited before interpreting benchmark results.

---

## Surprise 2 — llama3.2:3b Underperformed Predictions

Prior expectations suggested llama3.2:3b would demonstrate superior instruction-following behavior.

Instead:

| Temp | Pass Rate |
| ---- | --------- |
| 0.1  | 31.82%    |
| 0.7  | 22.73%    |
| 1.0  | 18.18%    |

The model consistently produced:

* invalid sentiment labels
* confidence calibration failures
* sarcasm detection errors

### Conclusion

The expected instruction-following advantage did not appear in this benchmark.

---

## Surprise 3 — qwen2.5:3b Toxicity Perfect Score

Across all temperatures:

* 100% toxicity accuracy

This was the most stable metric observed during the experiment.

Possible explanations:

1. Superior toxicity classification capability.
2. Toxicity examples were easier than sentiment examples.
3. Toxicity criteria aligned particularly well with Qwen's training.

### Conclusion

This result warrants further investigation in a future benchmark.

---

# Part 4 - What The Experiment Actually Measured

Although originally framed as a structured generation benchmark, the final implementation measured:

1. Sentiment classification
2. Toxicity classification
3. Confidence calibration
4. Sarcasm detection
5. Language identification
6. Structured schema adherence

The benchmark therefore evolved into a structured semantic classification benchmark.

This distinction is important when comparing Phase 3 results with earlier project phases.

---

# Part 5 - Decision 1 Revisited

## Original Decision

Phase 1 selected gemma2:2b as the preferred deployment model due to:

* low resource requirements
* strong structured generation performance
* favorable latency characteristics

Phase 3 was designed to challenge that decision.

## Evidence

### gemma2:2b

Strengths:

* Highest average quality score at temperature 0.1
* Strong sentiment accuracy
* Strong confidence calibration
* Excellent structural reliability
* Smallest model tested

Weaknesses:

* Largest performance degradation as temperature increased
* Consistent markdown fence behavior

### qwen2.5:3b

Strengths:

* Strongest temperature robustness
* Perfect toxicity accuracy
* Perfect structural validity
* Consistently high semantic quality

Weaknesses:

* Larger deployment footprint
* Slightly weaker sarcasm detection

### llama3.2:3b

Strengths:

* High structural reliability

Weaknesses:

* Lowest pass rates
* Weak confidence calibration
* Frequent invalid sentiment outputs
* No category-leading performance

## Final Recommendation

**Recommendation: gemma2:2b remains the primary deployment model for latency-constrained edge deployment.**

The model continues to provide the strongest balance between efficiency, reliability, and semantic quality.

**Recommendation: qwen2.5:3b becomes the preferred model when semantic quality, classification accuracy, and temperature robustness are the primary requirements.**

Phase 3 establishes qwen2.5:3b as a legitimate alternative deployment choice.

**Recommendation: llama3.2:3b is not recommended for either deployment profile based on current evidence.**

The model did not demonstrate a sufficient advantage in quality, reliability, or robustness to justify deployment over the competing models.

## Decision Status

Decision 1 remains unchanged.

However, Phase 3 significantly narrowed the gap between gemma2:2b and qwen2.5:3b and established qwen2.5:3b as the strongest challenger observed during the project.

---

# Part 6 - Open Questions

## Question 1

Why did qwen2.5:3b achieve perfect toxicity accuracy?

Is this a genuine capability advantage or a dataset artifact?

---

## Question 2

Why did llama3.2:3b generate so many invalid sentiment labels?

Future work should inspect raw outputs rather than relying solely on aggregate metrics.

---

## Question 3

Would qwen2.5:3b maintain its advantage under a nested schema benchmark?

Phase 3 used a relatively shallow schema.

A more complex structure may produce different rankings.

---

## Question 4

Why does gemma2:2b degrade more rapidly as temperature increases?

This was the steepest quality decline observed among the models.

---

## Question 5

How should adversarial examples be evaluated?

Fourteen inputs were intentionally excluded from scoring.

These inputs may contain the most meaningful differences between models and could require human evaluation rather than fixed labels.

---

# Final Conclusion

Phase 3 demonstrated that structural reliability is no longer the primary differentiator among modern small language models.

The dominant differences emerged from semantic interpretation, confidence calibration, and robustness to ambiguity.

gemma2:2b successfully defended its Phase 1 deployment recommendation.

qwen2.5:3b emerged as a serious challenger and the strongest alternative model observed during the project.

llama3.2:3b did not validate the hypothesis that stronger instruction-following would automatically translate into superior benchmark performance.

The benchmark therefore concludes with two viable deployment recommendations:

* gemma2:2b for efficiency-constrained deployment.
* qwen2.5:3b for quality-constrained deployment.
