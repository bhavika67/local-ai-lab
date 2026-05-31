# rescore.py
# Reloads phase3_results.jsonl and rescores with
# fixed language normalization (case-insensitive + aliases).
# Does NOT rerun the models.

import json
from collections import defaultdict


RESULTS_FILE = "phase3_results.jsonl"
LABEL_FILE = "quality_labels.json"

VALID_SENTIMENTS = {"positive", "negative", "neutral"}

LANGUAGE_ALIASES = {
    "english": {"english", "en", "en-us", "en-gb"},
    "other": {"other"}
}

MODELS = ["gemma2:2b", "llama3.2:3b", "qwen2.5:3b"]
TEMPERATURES = [0.1, 0.7, 1.0]


# ==========================================================
# LOADER
# ==========================================================

def load_labels(path):
    with open(path, "r", encoding="utf-8") as f:
        labels = json.load(f)
    return {item["id"]: item for item in labels}


# ==========================================================
# QUALITY SCORER (language fix applied)
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
        "errors": [],
        "failure_type": None
    }

    if model_output is None:
        result["errors"].append("generation_failed")
        result["failure_type"] = "generation_failure"
        result["passed"] = False
        return result

    expected = label["expected"]

    # --------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------

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

    # --------------------------------------------------
    # SARCASM
    # --------------------------------------------------

    result["sarcasm_correct"] = (
        model_output.get("contains_sarcasm")
        ==
        expected.get("contains_sarcasm")
    )

    if not result["sarcasm_correct"]:
        result["errors"].append("sarcasm_mismatch")

    # --------------------------------------------------
    # UNSCOREABLE INPUTS
    # --------------------------------------------------

    if not label["scoreable"]:
        result["passed"] = None
        result["overall_score"] = None
        return result

    # --------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------

    expected_sentiment = expected["sentiment"]
    actual_sentiment = model_output.get("sentiment")

    if actual_sentiment not in VALID_SENTIMENTS:
        result["sentiment_correct"] = False
        result["errors"].append("invalid_sentiment")
    else:
        result["sentiment_correct"] = (
            actual_sentiment == expected_sentiment
        )
        if not result["sentiment_correct"]:
            result["errors"].append("sentiment_mismatch")

    # --------------------------------------------------
    # TOXICITY
    # --------------------------------------------------

    expected_toxicity = expected["is_toxic"]
    actual_toxicity = model_output.get("is_toxic")

    result["toxicity_correct"] = (
        actual_toxicity == expected_toxicity
    )

    if not result["toxicity_correct"]:
        result["errors"].append("toxicity_mismatch")

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    low, high = expected["confidence_range"]
    confidence = model_output.get("confidence")

    if isinstance(confidence, (int, float)):
        result["confidence_in_range"] = (
            low <= confidence <= high
        )
    else:
        result["confidence_in_range"] = False

    if not result["confidence_in_range"]:
        result["errors"].append("confidence_out_of_range")

    # --------------------------------------------------
    # OVERALL SCORE
    # --------------------------------------------------

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

    # --------------------------------------------------
    # FAILURE TYPE
    # --------------------------------------------------

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
# RESCORE
# ==========================================================

def rescore():

    labels = load_labels(LABEL_FILE)
    summary = initialize_summary()

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            model_name = record["model"]
            temperature = record["temperature"]
            input_id = record["input_id"]

            model_output = record[
                "generation_result"
            ].get("final_output")

            label = labels[input_id]

            quality_result = score_quality(
                model_output, label, input_id
            )

            update_summary(
                summary, model_name, temperature, quality_result
            )

    return summary


# ==========================================================
# REPORTING
# ==========================================================

def print_summary(summary):

    print("\n")
    print("=" * 80)
    print("PHASE 3 RESCORED SUMMARY (language fix applied)")
    print("=" * 80)

    for model_name in MODELS:
        if model_name not in summary:
            continue

        print(f"\nMODEL: {model_name}")
        print("-" * 80)

        for temperature in TEMPERATURES:
            if temperature not in summary[model_name]:
                continue

            data = summary[model_name][temperature]
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

            print(f"\nTemperature: {temperature}")
            print(f"Runs: {data['runs']}")
            print(f"Scoreable: {data['scoreable_runs']} | "
                  f"Unscoreable: {data['unscoreable_runs']}")
            print("\n--- Quality Metrics (rescored) ---")
            print(f"Pass Rate:           {pass_rate:.2f}%")
            print(f"Avg Quality Score:   {avg_score:.3f}")
            print(f"Sentiment Accuracy:  {sentiment_acc:.2f}%")
            print(f"Toxicity Accuracy:   {toxicity_acc:.2f}%")
            print(f"Confidence Accuracy: {confidence_acc:.2f}%")
            print(f"Sarcasm Accuracy:    {sarcasm_acc:.2f}%")
            print(f"Language Accuracy:   {language_acc:.2f}%")

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
    summary = rescore()
    print_summary(summary)