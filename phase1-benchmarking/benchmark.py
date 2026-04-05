import time
import requests
import json

def benchmark_model(model_name, prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True
    }
    
    time_request_sent = time.time()
    time_first_token = None
    full_response = ""
    token_count = 0
    
    response = requests.post(url, json=payload, stream=True)
    
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line)
            
            if time_first_token is None:
                time_first_token = time.time()
            
            full_response += chunk["response"]
            token_count += 1
            
            if chunk["done"]:
                time_last_token = time.time()
                break
    
    ttft = time_first_token - time_request_sent
    total_latency = time_last_token - time_request_sent
    tokens_per_second = token_count / total_latency
    
    return {
        "model": model_name,
        "ttft_seconds": round(ttft, 3),
        "total_latency_seconds": round(total_latency, 3),
        "tokens_per_second": round(tokens_per_second, 2),
        "token_count": token_count
    }


def run_multiple_benchmarks(model_name, prompt, runs=5):
    results = []
    
    for i in range(runs):
        print(f"  Run {i+1} of {runs}...")
        result = benchmark_model(model_name, prompt)
        result["run_number"] = i + 1
        result["is_cold_start"] = i == 0
        results.append(result)
        print(f"  → TTFT: {result['ttft_seconds']}s | "
              f"Latency: {result['total_latency_seconds']}s | "
              f"TPS: {result['tokens_per_second']}")
        
        if i < runs - 1:
            print("  Cooling down 10 seconds...")
            time.sleep(10)
    
    cold_start = results[0]
    warm_runs = results[1:]
    
    avg_ttft = sum(r["ttft_seconds"] for r in warm_runs) / len(warm_runs)
    avg_latency = sum(r["total_latency_seconds"] for r in warm_runs) / len(warm_runs)
    avg_tps = sum(r["tokens_per_second"] for r in warm_runs) / len(warm_runs)
    
    return {
        "model": model_name,
        "cold_start": cold_start,
        "warm_average": {
            "ttft_seconds": round(avg_ttft, 3),
            "total_latency_seconds": round(avg_latency, 3),
            "tokens_per_second": round(avg_tps, 2)
        }
    }


# ---- RUN THE BENCHMARK ----

prompt = "Explain what a transformer architecture is in exactly 3 sentences."

print("\nBenchmarking phi3:mini...")
phi3_results = run_multiple_benchmarks("phi3:mini", prompt)

print("\nWaiting 30 seconds before next model...")
time.sleep(30)

print("\nBenchmarking gemma2:2b...")
gemma_results = run_multiple_benchmarks("gemma2:2b", prompt)

print("\n========== FINAL RESULTS ==========")
for r in [phi3_results, gemma_results]:
    print(f"\nModel: {r['model']}")
    print(f"  Cold Start TTFT:     {r['cold_start']['ttft_seconds']}s")
    print(f"  Warm Avg TTFT:       {r['warm_average']['ttft_seconds']}s")
    print(f"  Warm Avg Latency:    {r['warm_average']['total_latency_seconds']}s")
    print(f"  Warm Avg TPS:        {r['warm_average']['tokens_per_second']}")