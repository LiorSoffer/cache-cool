import time
import requests
import numpy as np
import os
import json
from dotenv import load_dotenv

load_dotenv()

URL = "http://localhost:8000/groq/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
}

prompts = [
    "What is the capital of Israel?",
    "What is the capital of Germany?",
    "What is the capital of Italy?",
    "What is the capital of Spain?",
    "What is the capital of Portugal?",
    "What is the capital of Greece?",
    "What is the capital of Turkey?",
    "Explain the significance of the Renaissance period in European history in detail",
    "Explain the middle east conflictin a paragraph",
    "Explain how to make pizza",
    "Explain the history of the internet",
]


def create_payload(prompt):
    return {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
    }


def send_request(payload, idx):
    start = time.time()
    res = requests.post(URL, json=payload, headers=HEADERS)
    duration = time.time() - start

    try:
        data = res.json()
        cache_status = data.get("cache_status", "MISS")
        if cache_status == "HIT":
            status_indicator = "🟢 HIT"
            cache_hit = True
        else:
            status_indicator = "🔴 MISS"
            cache_hit = False
    except Exception as e:
        print(f"Error parsing response: {e}")
        status_indicator = "❌ ERROR"
        cache_hit = False

    print(f"Request {idx} took {duration:.3f}s - {status_indicator}")
    return duration, cache_hit


def run_test(test_prompts_order):
    latencies = []
    cache_hits = 0
    cache_misses = 0

    for idx in test_prompts_order:
        prompt = prompts[idx]
        payload = create_payload(prompt)
        latency, hit = send_request(payload, idx)
        latencies.append(latency)
        if hit:
            cache_hits += 1
        else:
            cache_misses += 1
    return latencies, cache_hits, cache_misses


def run_and_report_test(test_order):
    """Run a test and print results"""
    print("Test order: ", test_order)
    clear_cache()
    latencies, cache_hits, cache_misses = run_test(test_order)
    total = cache_hits + cache_misses
    hit_rate = cache_hits / total if total > 0 else 0
    print(f"Hit rate: {hit_rate:.1%} ({cache_hits} hits, {cache_misses} misses)")
    print("================================================")
    return latencies, cache_hits, cache_misses


def clear_cache():
    if os.path.exists("cache.json"):
        os.remove("cache.json")


def save_detailed_results(filename, test_name, test_order, latencies, hits):
    with open(filename, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for idx, latency in zip(test_order, latencies):
            writer.writerow([test_name, prompts[idx], idx, latency, hits[idx]])


import json


def main():
    print("Starting benchmark...")

    # Run tests
    test1_order = [1, 2, 3, 4, 5, 1, 6, 1, 7, 1]
    latencies1, cache_hits1, cache_misses1 = run_and_report_test(test1_order)

    test2_order = [4, 5, 6, 7, 8, 9, 5, 6, 4, 6, 5, 6]
    latencies2, cache_hits2, cache_misses2 = run_and_report_test(test2_order)

    test3_order = [8, 10, 7, 3, 2, 7, 8, 6, 5, 4, 7, 8, 8]
    latencies3, cache_hits3, cache_misses3 = run_and_report_test(test3_order)

    # Combine all results
    all_latencies = latencies1 + latencies2 + latencies3
    total_hits = cache_hits1 + cache_hits2 + cache_hits3
    total_misses = cache_misses1 + cache_misses2 + cache_misses3
    total_requests = total_hits + total_misses
    latencies_np = np.array(all_latencies)
    overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0

    # Metrics
    mean_latency = latencies_np.mean()
    p95_latency = np.percentile(latencies_np, 95)
    p99_latency = np.percentile(latencies_np, 99)

    # Summary print
    print("\n=== Overall Benchmark Summary ===")
    print(f"Total Requests: {total_requests}")
    print(f"Cache Hits: {total_hits}")
    print(f"Cache Misses: {total_misses}")
    print(f"Overall Hit Rate: {overall_hit_rate:.2%}")
    print(f"Mean Latency: {mean_latency:.3f}s")
    print(f"95th Percentile Latency: {p95_latency:.3f}s")
    print(f"99th Percentile Latency: {p99_latency:.3f}s")

    # Save to JSON
    results = {
        "total_requests": total_requests,
        "cache_hits": total_hits,
        "cache_misses": total_misses,
        "overall_hit_rate": round(overall_hit_rate, 4),
        "mean_latency_sec": round(mean_latency, 4),
        "p95_latency_sec": round(p95_latency, 4),
        "p99_latency_sec": round(p99_latency, 4),
        "all_latencies_sec": [round(x, 4) for x in all_latencies],
    }

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("📁 Benchmark results saved to 'benchmark_results.json'")


if __name__ == "__main__":
    main()
