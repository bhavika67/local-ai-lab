# run_phase3_experiment.py

import json
from collections import defaultdict

from structured_generation import generate_with_validation


# ==========================================================
# CONFIG
# ==========================================================

MODELS = [
    "gemma2:2b",
    "llama3.2:3b",
    "qwen2.5:3b"
]

TEMPERATURES = [0.1, 0.7, 1.0]

INPUT_FILE = "inputs_phase3.json"
LABEL_FILE = "quality_labels.json"
OUTPUT_FILE = "phase3_results.jsonl"

SCHEMA = {
    "sentiment": str,
    "confidence": float,
    "is_toxic": bool,
    "toxicity_confidence": float,
    "contains_sarcasm": bool,
    "language": str,
    "reasoning": str
}

VALID_SENTIMENTS = {
    "positive",
    "negative",
    "neutral"
}

LANGUAGE_ALIASES = {
    "english": {"english", "en", "en-us", "en-gb"},
    "other": {"other"}
}


# ==========================================================
# LOADERS
# ==========================================================

def load_inputs(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_labels(path):

    with open(path, "r", encoding="utf-8") as f:
        labels = json.load(f)

    return {
        item["id"]: item
        for item in labels
    }


# ==========================================================
# QUALITY SCORING
# ==========================================================

def score_quality(model_output, label, input_id):

    result = {
        "input_id": input_id,
        "scoreable": label["scoreable"],
        "overall_score": None,
        "passed": None,
        "sentiment_correct": None,
        "toxicity_correct": None,
        "confidence_in_range": None,
        "sarcasm_correct": None,
        "language_correct": None,
        "expected_sentiment": None,
        "expected_toxicity": None,
        "expected_confidence_range": None,
        "expected_sarcasm": None,
        "expected_language": None,
        "actual_sentiment": None,
        "actual_toxicity": None,
        "actual_confidence": None,
        "actual_sarcasm": None,
        "actual_language": None,
        "errors": [],
        "failure_type": None
    }

    if model_output is None:
        result["errors"].append("generation_failed")
        result["failure_type"] = "generation_failure"
        result["passed"] = False
        return result

    expected = label["expected"]

    result["actual_sentiment"] = model_output.get("sentiment")
    result["actual_toxicity"] = model_output.get("is_toxic")
    result["actual_confidence"] = model_output.get("confidence")
    result["actual_sarcasm"] = model_output.get("contains_sarcasm")
    result["actual_language"] = model_output.get("language")
    result["expected_sarcasm"] = expected.get("contains_sarcasm")
    result["expected_language"] = expected.get("language")

    # ------------------------------------------------------
    # LANGUAGE — fixed: case-insensitive + alias matching
    # ------------------------------------------------------

    actual_language = str(
        model_output.get("language", "")
    ).lower().strip()

    expected_language = str(
        expected.get("language", "")
    ).lower().strip()

    accepted = LANGUAGE_ALIASES.get(
        expected_language,
        {expected_language}
    )

    result["language_correct"] = (
        actual_language in accepted
    )

    if not result["language_correct"]:
        result["errors"].append("language_mismatch")

    # ------------------------------------------------------
    # SARCASM
    # ------------------------------------------------------

    result["sarcasm_correct"] = (
        model_output.get("contains_sarcasm")
        ==
        expected.get("contains_sarcasm")
    )

    if not result["sarcasm_correct"]:
        result["errors"].append("sarcasm_mismatch")

    # ------------------------------------------------------
    # UNSCOREABLE INPUTS
    # ------------------------------------------------------

    if not label["scoreable"]:
        result["passed"] = None
        result["overall_score"] = None
        return result

    # ------------------------------------------------------
    # SENTIMENT
    # ------------------------------------------------------

    expected_sentiment = expected["sentiment"]
    actual_sentiment = model_output.get("sentiment")

    result["expected_sentiment"] = expected_sentiment
    result["actual_sentiment"] = actual_sentiment

    if actual_sentiment not in VALID_SENTIMENTS:
        result["sentiment_correct"] = False
        result["errors"].append("invalid_sentiment")
    else:
        result["sentiment_correct"] = (
            actual_sentiment == expected_sentiment
        )
        if not result["sentiment_correct"]:
            result["errors"].append("sentiment_mismatch")

    # ------------------------------------------------------
    # TOXICITY
    # ------------------------------------------------------

    expected_toxicity = expected["is_toxic"]
    actual_toxicity = model_output.get("is_toxic")

    result["expected_toxicity"] = expected_toxicity
    result["actual_toxicity"] = actual_toxicity

    result["toxicity_correct"] = (
        actual_toxicity == expected_toxicity
    )

    if not result["toxicity_correct"]:
        result["errors"].append("toxicity_mismatch")

    # ------------------------------------------------------
    # CONFIDENCE
    # ------------------------------------------------------

    low, high = expected["confidence_range"]
    result["expected_confidence_range"] = [low, high]

    confidence = model_output.get("confidence")
    result["actual_confidence"] = confidence

    if isinstance(confidence, (int, float)):
        result["confidence_in_range"] = (
            low <= confidence <= high
        )
    else:
        result["confidence_in_range"] = False

    if not result["confidence_in_range"]:
        result["errors"].append("confidence_out_of_range")

    # ------------------------------------------------------
    # OVERALL SCORE
    # ------------------------------------------------------

    component_scores = [
        int(result["sentiment_correct"]),
        int(result["toxicity_correct"]),
        int(result["confidence_in_range"]),
        int(result["sarcasm_correct"]),
        int(result["language_correct"])
    ]

    result["overall_score"] = round(
        sum(component_scores) / len(component_scores), 3
    )

    result["passed"] = (
        result["sentiment_correct"]
        and result["toxicity_correct"]
        and result["confidence_in_range"]
    )

    # ------------------------------------------------------
    # FAILURE TYPE
    # ------------------------------------------------------

    if result["passed"]:
        result["failure_type"] = None
    elif len(result["errors"]) > 1:
        result["failure_type"] = "multiple"
    else:
        result["failure_type"] = result["errors"][0]

    return result


# ==========================================================
# SUMMARY
# ==========================================================

def initialize_summary():

    return defaultdict(
        lambda: defaultdict(
            lambda: {
                "runs": 0,
                "first_pass_valid": 0,
                "final_valid": 0,
                "recovery": 0,
                "fence_detected": 0,
                "scoreable_runs": 0,
                "unscoreable_runs": 0,
                "passed": 0,
                "sentiment_correct": 0,
                "toxicity_correct": 0,
                "confidence_correct": 0,
                "sarcasm_correct": 0,
                "language_correct": 0,
                "overall_scores": [],
                "failure_types": defaultdict(int),
                "error_counts": defaultdict(int)
            }
        )
    )


def update_summary(summary, model_name, temperature, quality_result):

    bucket = summary[model_name][temperature]
    bucket["runs"] += 1

    if quality_result["scoreable"]:
        bucket["scoreable_runs"] += 1
    else:
        bucket["unscoreable_runs"] += 1

    if quality_result["passed"]:
        bucket["passed"] += 1

    if quality_result["sentiment_correct"]:
        bucket["sentiment_correct"] += 1

    if quality_result["toxicity_correct"]:
        bucket["toxicity_correct"] += 1

    if quality_result["confidence_in_range"]:
        bucket["confidence_correct"] += 1

    if quality_result["sarcasm_correct"]:
        bucket["sarcasm_correct"] += 1

    if quality_result["language_correct"]:
        bucket["language_correct"] += 1

    if quality_result["overall_score"] is not None:
        bucket["overall_scores"].append(
            quality_result["overall_score"]
        )

    failure_type = quality_result.get("failure_type")
    if failure_type:
        bucket["failure_types"][failure_type] += 1

    for error in quality_result["errors"]:
        bucket["error_counts"][error] += 1


# ==========================================================
# RUNNER
# ==========================================================

def run_experiment(output_handle):

    inputs = load_inputs(INPUT_FILE)
    labels = load_labels(LABEL_FILE)
    summary = initialize_summary()
    run_id = 0

    for model_name in MODELS:

        for temperature in TEMPERATURES:

            print(f"\nMODEL={model_name} TEMP={temperature}")

            for item in inputs:

                run_id += 1
                input_id = item["id"]
                text = item["text"]
                label = labels[input_id]

                result = generate_with_validation(
                    model=model_name,
                    task=text,
                    schema=SCHEMA,
                    temperature=temperature
                )

                # ----------------------------------
                # STRUCTURAL METRICS
                # ----------------------------------

                bucket = summary[model_name][temperature]

                attempt_1_validation = (
                    result["attempt_1_result"]["validation_result"]
                )

                if attempt_1_validation["is_valid"]:
                    bucket["first_pass_valid"] += 1

                if result["final_valid"]:
                    bucket["final_valid"] += 1

                if result["recovery"]:
                    bucket["recovery"] += 1

                if attempt_1_validation.get("fence_detected"):
                    bucket["fence_detected"] += 1

                # ----------------------------------
                # QUALITY SCORING
                # ----------------------------------

                model_output = result.get("final_output")

                quality_result = score_quality(
                    model_output, label, input_id
                )

                update_summary(
                    summary, model_name, temperature, quality_result
                )

                # ----------------------------------
                # LOG RECORD
                # ----------------------------------

                record = {
                    "run_id": run_id,
                    "model": model_name,
                    "temperature": temperature,
                    "input_id": input_id,
                    "input_text": text,
                    "quality_result": quality_result,
                    "generation_result": result
                }

                output_handle.write(json.dumps(record) + "\n")
                output_handle.flush()

    return summary


# ==========================================================
# REPORTING
# ==========================================================

def print_summary(summary):

    print("\n")
    print("=" * 80)
    print("PHASE 3 SUMMARY")
    print("=" * 80)

    for model_name, temps in summary.items():

        print(f"\nMODEL: {model_name}")
        print("-" * 80)

        for temperature, data in temps.items():

            scoreable = max(data["scoreable_runs"], 1)

            pass_rate = (data["passed"] / scoreable) * 100
            sentiment_acc = (data["sentiment_correct"] / scoreable) * 100
            toxicity_acc = (data["toxicity_correct"] / scoreable) * 100
            confidence_acc = (data["confidence_correct"] / scoreable) * 100
            sarcasm_acc = (data["sarcasm_correct"] / data["runs"]) * 100
            language_acc = (data["language_correct"] / data["runs"]) * 100

            avg_score = (
                sum(data["overall_scores"]) / len(data["overall_scores"])
                if data["overall_scores"] else 0
            )

            first_pass_rate = (
                data["first_pass_valid"] / data["runs"]
            ) * 100

            final_valid_rate = (
                data["final_valid"] / data["runs"]
            ) * 100

            first_pass_failures = (
                data["runs"] - data["first_pass_valid"]
            )

            recovery_rate = (
                (data["recovery"] / first_pass_failures) * 100
                if first_pass_failures > 0
                else 0
            )

            fence_rate = (data["fence_detected"] / data["runs"]) * 100

            print(f"\nTemperature: {temperature}")
            print(f"Runs: {data['runs']}")
            print(
                f"Scoreable: {data['scoreable_runs']} | "
                f"Unscoreable: {data['unscoreable_runs']}"
            )

            print("\n--- Structural Metrics ---")
            print(f"First-pass Valid Rate: {first_pass_rate:.2f}%")
            print(f"Final Valid Rate:      {final_valid_rate:.2f}%")
            print(f"Recovery Rate:         {recovery_rate:.2f}%")
            print(f"Fence Detection Rate:  {fence_rate:.2f}%")
            print(f"Recoveries:            {data['recovery']}")
            print(f"Fence Detections:      {data['fence_detected']}")

            print("\n--- Quality Metrics ---")
            print(f"Pass Rate:           {pass_rate:.2f}%")
            print(f"Average Score:       {avg_score:.3f}")
            print(f"Sentiment Accuracy:  {sentiment_acc:.2f}%")
            print(f"Toxicity Accuracy:   {toxicity_acc:.2f}%")
            print(f"Confidence Accuracy: {confidence_acc:.2f}%")
            print(f"Sarcasm Accuracy:    {sarcasm_acc:.2f}%")
            print(f"Language Accuracy:   {language_acc:.2f}%")

            print("\nFailure Types:")
            if data["failure_types"]:
                for ft, count in sorted(
                    data["failure_types"].items(),
                    key=lambda x: x[1],
                    reverse=True
                ):
                    print(f"  {ft}: {count}")
            else:
                print("  None")

            print("\nTop Errors:")
            if data["error_counts"]:
                for error, count in sorted(
                    data["error_counts"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]:
                    print(f"  {error}: {count}")
            else:
                print("  None")

        print("\n" + "=" * 80)


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    with open(OUTPUT_FILE, "w", encoding="utf-8") as output_file:
        summary = run_experiment(output_file)

    print_summary(summary)