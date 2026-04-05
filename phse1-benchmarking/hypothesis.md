# Phase 1 - Benchmarking Hypothesis
Date: 2026-04-05

## My Setup
- Device: Dell Inspiron 15 3520
- CPU: Intel i5-1235U (mobile, low power)
- RAM: 24GB
- GPU: None (CPU inference only)
- Models: phi3:mini (3.8B), gemma2:2b (2B)

## Hypothesis 1 - Token Speed
gemma2:2b will be faster than phi3:mini 
because it has fewer parameters.

Reasoning: More parameters means more matrix 
multiplications per token which means more 
compute required. Fewer parameters = less work 
per token = faster generation.

## Hypothesis 2 - Estimated Token Speed Range
gemma2:2b: I expect 10 to 15 tokens/second
phi3:mini: I expect 3 to 10 tokens/second

Reasoning: CPU inference on quantized models 
typically falls between 3-15 tokens/second. 
gemma2:2b gets the upper half because it has 
fewer parameters. phi3:mini gets the lower half 
because it has more parameters and requires 
more compute per token.

## Hypothesis 3 - Instruction Following
The model will sometimes follow the 3 sentence 
constraint but not always.

Reasoning: These models don't think like humans. 
They do pattern matching — predicting the next 
token based on training data. They have no 
internal counter for sentences. "Exactly 3 
sentences" requires self-monitoring during 
generation which pattern matching does not 
guarantee.

## Concepts Learned Before Running Any Code

### Thermal Throttling
When a CPU computes continuously it generates 
heat. When heat builds up faster than the 
cooling system can dissipate it, the CPU quietly 
reduces its own clock speed to stay safe.

Example on my machine:
- Minute 0:  3.8 GHz boost → ~12 tokens/second
- Minute 5:  2.1 GHz       → ~7 tokens/second
- Minute 10: 1.3 GHz base  → ~4 tokens/second

Same model. Same prompt. Three different numbers.
This means my benchmark timing matters — a cold 
start gives best case numbers, sustained runs 
give worst case numbers.

## What I Don't Know Yet
- Actual token speeds on my specific CPU
- Whether thermal throttling will affect my 
  results significantly
- Whether my numbers will be cold-start or 
  throttled-state numbers
- Which model produces better quality answers
- How to design benchmarks that account for 
  thermal state