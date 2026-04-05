# Phase 1 - Benchmarking Hypothesis
Date: 2026-04-05
Device: Dell Inspiron 15 3520 | i5-1235U | 24GB RAM | No GPU

---

## My Setup

| Component | Details |
|-----------|---------|
| Device    | Dell Inspiron 15 3520 |
| CPU       | Intel i5-1235U (mobile, low power, 1.30 GHz base) |
| RAM       | 24GB |
| GPU       | None — CPU inference only |
| Models    | phi3:mini (3.8B params), gemma2:2b (2B params) |

---

## Hypothesis 1 - Which Model Will Be Faster?

**Prediction:** gemma2:2b will generate tokens faster than phi3:mini

**Reasoning:** More parameters means more matrix multiplications
per token, which means more compute required per token.
Fewer parameters = less work per token = faster generation.

  phi3:mini  → 3.8B parameters → more compute → slower
  gemma2:2b  → 2.0B parameters → less compute → faster

---

## Hypothesis 2 - Expected Token Speed Range

**Prediction:**
- gemma2:2b: 10 to 15 tokens/second
- phi3:mini:  3 to 10 tokens/second

**Reasoning:** CPU inference on quantized models typically falls
between 3-15 tokens/second. gemma2:2b gets the upper half
because it has fewer parameters. phi3:mini gets the lower half
because it has more parameters and requires more compute per token.

---

## Hypothesis 3 - Instruction Following

**Prediction:** Models will sometimes follow the "exactly 3 sentences"
constraint but not always — behavior will be inconsistent.

**Reasoning:** These models do not think like humans. They do pattern
matching — predicting the next token based on training data.
They have no internal counter tracking how many sentences they
have written. "Exactly 3 sentences" requires self-monitoring
during generation, which pattern matching does not guarantee.

---

## Concepts Learned Before Running Any Code

### Quantization
Models are compressed from full precision (32-bit or 16-bit
floating point numbers) down to 4-bit integers. This makes them:
- Smaller on disk
- Faster to load into memory
- Slightly lower quality than full precision
- Possible to run on consumer hardware

Without quantization a 7B model would need ~28GB RAM.
With 4-bit quantization it needs only ~4GB.

### What a Model Actually Is On Disk
A model is not one file. When Ollama downloads a model it pulls
several separate components:

| Component  | Purpose |
|------------|---------|
| Weights    | The actual learned parameters (largest file) |
| Tokenizer  | Converts text → numbers → text |
| Config     | Architecture settings |
| Template   | How prompts should be formatted for this model |

This matters because different models have different tokenizers.
The same prompt can produce different numbers of tokens on
different models. This makes raw tokens/second an unfair
cross-model comparison metric.

### Thermal Throttling
When a CPU computes continuously it generates heat. When heat
builds up faster than the cooling system can dissipate it,
the CPU quietly reduces its own clock speed to stay safe.
This is called thermal throttling.

Example on my machine during sustained inference:

| Time     | Clock Speed | Est. Tokens/Second |
|----------|-------------|-------------------|
| Minute 0  | 3.8 GHz boost | ~12 t/s |
| Minute 5  | 2.1 GHz       | ~7 t/s  |
| Minute 10 | 1.3 GHz base  | ~4 t/s  |

Same model. Same prompt. Three completely different numbers.
This means benchmark timing matters — cold start gives best
case numbers, sustained runs give throttled numbers.
Always specify which state your benchmark was measured in.

### Cold Start vs Warm Start
- Cold start = model not yet loaded in memory
- Warm start = model already loaded and ready
- Cold start produces much higher TTFT than warm start
- Benchmarks must always specify which state was measured
### Why Wrap Ollama in FastAPI
Ollama exposes a raw API on port 11434.
FastAPI sits in front of it and adds:
- Single point for logging every request
- Single point for validation and retry logic
- Authentication layer if needed
- Consistent response format for all clients
- Ability to add features without changing clients

This pattern is called a proxy or middleware layer.
It is how production ML systems are structured.

---

## What I Don't Know Yet
- What actually happens in memory when a model loads
- What exactly causes the delay before the first token appears
- How much thermal throttling will affect my specific results
- Whether my benchmark runs are cold start or warm start
- Which model produces better quality answers
- How to design benchmarks that properly account for thermal state
- Whether tokens/second is even the right metric to compare models