# Phase 1 - Benchmarking Observations
Date: 2026-04-05
Device: Dell Inspiron 15 3520 | i5-1235U | 24GB RAM | No GPU
Prompt: "Explain what a transformer architecture is in exactly 3 sentences."

---

## Part 1 - Manual Run (No Measurement Tools)

First impressions before any code was written.
Both models were run manually via `ollama run` in the terminal.

| Observation          | phi3:mini                  | gemma2:2b                  |
|----------------------|----------------------------|----------------------------|
| Speed feel           | Slower                     | Faster                     |
| Followed 3 sentences | YES                        | YES                        |
| Sentence style       | Shorter, simpler sentences | Longer, denser sentences   |

---

## Part 2 - Pre-Benchmark Math (Estimates Before Measuring)

Before running any code, we estimated response times using:

```
total_time = (word_count × 1.3) ÷ tokens_per_second
```

| Model     | Est. Words | Est. Tokens | Est. Speed | Est. Total Time |
|-----------|------------|-------------|------------|-----------------|
| phi3:mini | ~60        | ~78         | 6 t/s      | ~13 seconds     |
| gemma2:2b | ~80        | ~104        | 12 t/s     | ~8.6 seconds    |

Implication: Even though gemma was expected to generate more words,
it was predicted to finish faster because its speed advantage
outweighs its longer output length.

---

## Part 3 - Single Run Benchmark Results

Script: benchmark.py | Method: streaming API with time.time() timestamps

| Metric              | phi3:mini | gemma2:2b |
|---------------------|-----------|-----------|
| TTFT (seconds)      | 4.838     | 4.871     |
| Total Latency (sec) | 24.513    | 11.465    |
| Tokens/second       | 6.40      | 6.72      |
| Token count         | 157       | 77        |

---

## Part 4 - Multi-Run Benchmark Results

Each model was run 5 times with 10 second cooldowns between runs.
Run 1 = cold start. Runs 2-5 = warm start. Averages exclude run 1.

### phi3:mini — All Runs

| Run | Cold Start | TTFT    | Latency  | TPS  |
|-----|------------|---------|----------|------|
| 1   | YES        | 22.704s | 40.059s  | 3.40 |
| 2   | NO         | 6.070s  | 21.444s  | 5.74 |
| 3   | NO         | 4.992s  | 18.859s  | 5.73 |
| 4   | NO         | 8.962s  | 25.884s  | 4.79 |
| 5   | NO         | 2.215s  | 17.980s  | 5.23 |

| Summary             | Value   |
|---------------------|---------|
| Cold Start TTFT     | 22.704s |
| Warm Avg TTFT       | 5.560s  |
| Warm Avg Latency    | 21.042s |
| Warm Avg TPS        | 5.37    |

### gemma2:2b — All Runs

| Run | Cold Start | TTFT   | Latency  | TPS  |
|-----|------------|--------|----------|------|
| 1   | YES        | 2.417s | 7.878s   | 8.76 |
| 2   | NO         | 2.406s | 8.609s   | 8.83 |
| 3   | NO         | 2.407s | 8.481s   | 8.73 |
| 4   | NO         | 2.405s | 10.298s  | 8.35 |
| 5   | NO         | 2.406s | 9.404s   | 8.40 |

| Summary             | Value  |
|---------------------|--------|
| Cold Start TTFT     | 2.417s |
| Warm Avg TTFT       | 2.406s |
| Warm Avg Latency    | 9.198s |
| Warm Avg TPS        | 8.58   |

---

## Part 5 - Surprise Findings

### Surprise 1 - Single Run Results Were Misleading
Single run showed TPS of 6.40 vs 6.72 — nearly identical.
Five run averages revealed 5.37 vs 8.58 — gemma is 60% faster.

Lesson: Never trust a single benchmark run. Variance is real
and single measurements hide it completely.

### Surprise 2 - phi3 Cold Start Penalty Was Massive
phi3 cold start TTFT: 22.704s
phi3 warm avg TTFT:   5.560s
Difference:           17.144 seconds

Cause: phi3 must load 2.2GB of weights from disk into RAM
before generating the first token. This takes ~17 extra seconds
on a cold start compared to a warm start.

gemma had almost no cold start penalty (2.417s vs 2.406s warm)
because its smaller 1.6GB size loads fast enough to be negligible.

### Surprise 3 - phi3 Warm TTFT Was Inconsistent
phi3 warm TTFT across runs: 6.07s → 4.99s → 8.96s → 2.21s
gemma warm TTFT across runs: 2.406s → 2.407s → 2.405s → 2.406s

phi3 spiked to 8.96s on run 4 after sustained inference.
This is thermal throttling made visible in real data.

Cause: CPU accumulated heat across consecutive runs.
10 second cooldown was not enough for phi3's longer inference time.
gemma's shorter runs generated less heat per run, avoiding throttling.

Lesson: Unpredictable latency feels worse to a user than
consistently slow latency. gemma's rock-solid TTFT consistency
is a production advantage beyond just raw speed.

### Surprise 4 - Tokenizer Difference Explains Token Counts
phi3 generated 157 tokens | gemma generated 77 tokens
Both responses were similar in actual content length.

Cause: Different tokenizers break the same words into
different sized pieces.

Example:
- phi3 might tokenize: "transformer" → "trans" + "form" + "er" = 3 tokens
- gemma might tokenize: "transformer" → "transformer"           = 1 token

Critical implication: tokens/second is NOT a fair cross-model
comparison metric. A model that uses more tokens to express
the same content will always appear slower in TPS even if
it delivers equivalent information in less total time.

Better metric: total_latency for equivalent quality responses.

---

## Part 6 - What My Hypothesis Got Wrong

| Hypothesis                 | Expected    | Reality     | Lesson                                  |
|----------------------------|-------------|-------------|-----------------------------------------|
| gemma faster TPS           | 10-15 t/s   | 8.58 t/s    | Hardware ceiling limits both models     |
| phi3 slower TPS            | 3-10 t/s    | 5.37 t/s    | Same ceiling applies regardless of size |
| similar TTFT (single run)  | gemma faster | nearly equal | Single runs hide real differences      |
| pre-benchmark latency math | gemma ~8.6s | gemma 9.198s | Estimates need real measurement        |

---

## Part 7 - Key Concepts Learned

### TTFT vs Total Latency
- TTFT = time from request sent to first token received
- Total latency = time from request sent to last token received
- High TTFT makes system feel broken or frozen
- High total latency makes system feel slow but alive
- Always measure and report these separately

### Cold Start vs Warm Start
- Cold start = model not loaded in memory → high TTFT
- Warm start = model already loaded → low TTFT
- Always specify which state your benchmark was measured in
- For edge deployment, warm start is the normal user experience

### Thermal Throttling
- CPU reduces clock speed to manage heat under sustained load
- Affects benchmark numbers silently — you cannot see it happening
- phi3 showed clear throttling spike on run 4
- 10 second cooldown insufficient for phi3 on i5-1235U
- gemma thermally stable due to shorter inference time per run

### Tokenization
- Different models use different tokenizers
- Same text produces different token counts across models
- Makes tokens/second an unreliable cross-model metric
- Total latency for equivalent responses is the fairer metric

---

## Part 8 - Open Questions For Next Phases

- How do both models perform on longer, more complex prompts?
- Does prompt length significantly change TTFT?
- How does performance change under concurrent requests?
- Is gemma output quality good enough for real use cases?
- How much cooldown time is actually needed for phi3 stability?
- Do these results hold under 30+ minutes of sustained load?