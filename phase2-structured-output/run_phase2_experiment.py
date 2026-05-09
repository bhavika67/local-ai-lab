# run_phase2_experiment.py

import json
from collections import Counter, defaultdict

from structured_generation import (
    generate_with_validation
)


# ==========================================================
# CONFIG
# ==========================================================

MODEL_NAME = "gemma2:2b"

TEMPERATURES = [0.1, 0.4, 0.7, 1.0]

OUTPUT_FILE = "phase2_results.jsonl"

SCHEMA = {
    "sentiment": str,
    "confidence": float,
    "is_toxic": bool
}


# ==========================================================
# LOAD INPUTS
# ==========================================================

with open("inputs.json", "r") as f:
    input_texts = json.load(f)


# ==========================================================
# METRICS
# ==========================================================

summary = defaultdict(lambda: {
    "runs": 0,
    "first_pass_valid": 0,
    "final_valid": 0,
    "recovery": 0,
    "fence_detected": 0,
    "failure_modes": Counter()
})


# ==========================================================
# RUN EXPERIMENT
# ==========================================================

run_id = 0

for temperature in TEMPERATURES:

    print(f"\n{'=' * 60}")
    print(f"RUNNING TEMPERATURE: {temperature}")
    print(f"{'=' * 60}\n")

    for input_text in input_texts:

        run_id += 1

        print(
            f"[Run {run_id}] "
            f"Temperature={temperature}"
        )

        result = generate_with_validation(
            model=MODEL_NAME,
            task=input_text,
            schema=SCHEMA,
            temperature=temperature
        )

        attempt_1 = result["attempt_1_result"]

        validation_1 = attempt_1[
            "validation_result"
        ]

        attempt_2 = result.get(
            "attempt_2_result"
        )

        # --------------------------------------------------
        # SUMMARY METRICS
        # --------------------------------------------------

        summary[temperature]["runs"] += 1

        if validation_1["is_valid"]:
            summary[temperature][
                "first_pass_valid"
            ] += 1

        if result["final_valid"]:
            summary[temperature][
                "final_valid"
            ] += 1

        if result["recovery"]:
            summary[temperature][
                "recovery"
            ] += 1
        
        if validation_1.get("fence_detected"):
            summary[temperature]["fence_detected"] += 1

        for failure_mode in validation_1[
            "failure_modes"
        ]:

            summary[temperature][
                "failure_modes"
            ][failure_mode] += 1

        # --------------------------------------------------
        # WRITE JSONL RECORD
        # --------------------------------------------------

        record = {
            "run_id": run_id,
            "temperature": temperature,
            "input_text": input_text,
            "result": result
        }

        with open(OUTPUT_FILE, "a") as f:

            f.write(
                json.dumps(record) + "\n"
            )

        print(
            f"  Final Valid: {result['final_valid']} | "
            f"Recovery: {result['recovery']}"
        )


# ==========================================================
# FINAL SUMMARY
# ==========================================================

print(f"\n{'=' * 60}")
print("FINAL SUMMARY")
print(f"{'=' * 60}")

for temperature in TEMPERATURES:

    data = summary[temperature]

    runs = data["runs"]

    first_pass_valid_rate = round(
        (data["first_pass_valid"] / runs) * 100,
        2
    )

    final_valid_rate = round(
        (data["final_valid"] / runs) * 100,
        2
    )

    first_pass_failures = runs - data["first_pass_valid"]
    
    recovery_rate = round(
    (data["recovery"] / first_pass_failures * 100)
    if first_pass_failures > 0
    else 0,
    2
)

    print(f"\nTemperature: {temperature}")

    print(
        f"First-pass valid rate: "
        f"{first_pass_valid_rate}%"
    )

    print(
        f"Final valid rate: "
        f"{final_valid_rate}%"
    )

    print(
        f"Recovery rate: "
        f"{recovery_rate}%"
    )

    print("Failure mode distribution:")

    for mode, count in data[
        "failure_modes"
    ].items():

        percentage = round(
            (count / runs) * 100,
            2
        )

        print(
            f"  - {mode}: "
            f"{count} ({percentage}%)"
        )