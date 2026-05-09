# structured_generation.py

import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark import benchmark_model


# ==========================================================
# VALIDATION
# ==========================================================

def validate_structured_response(response_string, schema):

    result = {
    "is_valid": True,
    "failure_modes": [],
    "missing_fields": [],
    "wrong_type_fields": [],
    "parsed": None,
    "fence_detected": False
}

    # ------------------------------------------------------
    # STEP 0 — DETECT AND STRIP MARKDOWN FENCES
    # ------------------------------------------------------

    cleaned = response_string.strip()

    if cleaned.startswith("```"):
        result["fence_detected"] = True
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]).strip()

    # ------------------------------------------------------
    # STEP 1 — PARSE JSON
    # ------------------------------------------------------

    try:
        parsed = json.loads(cleaned)
        result["parsed"] = parsed

    except json.JSONDecodeError as e:

        result["is_valid"] = False

        result["failure_modes"].append("syntax")

        result["syntax_error"] = {
            "message": str(e),
            "line": e.lineno,
            "column": e.colno
        }

        return result

    # ------------------------------------------------------
    # STEP 2 — CHECK REQUIRED FIELDS
    # ------------------------------------------------------

    for field in schema:

        if field not in parsed:
            result["missing_fields"].append(field)

    if result["missing_fields"]:

        result["is_valid"] = False

        if "missing_field" not in result["failure_modes"]:
            result["failure_modes"].append("missing_field")

    # ------------------------------------------------------
    # STEP 3 — CHECK FIELD TYPES
    # ------------------------------------------------------

    for field, expected_type in schema.items():

        # skip missing fields
        if field not in parsed:
            continue

        value = parsed[field]

        # --------------------------------------------------
        # ACCEPT int AS VALID float
        # JSON numbers do not strongly separate int/float
        # --------------------------------------------------

        if expected_type is float and type(value) is int:
            continue

        # --------------------------------------------------
        # PREVENT bool PASSING AS int
        # bool is subclass of int in Python
        # --------------------------------------------------

        if expected_type is int and type(value) is bool:

            result["wrong_type_fields"].append({
                "field": field,
                "expected": "int",
                "actual": "bool",
                "value": value
            })

            continue

        # --------------------------------------------------
        # STRICT TYPE CHECK
        # --------------------------------------------------

        if type(value) is not expected_type:

            result["wrong_type_fields"].append({
                "field": field,
                "expected": expected_type.__name__,
                "actual": type(value).__name__,
                "value": value
            })

    if result["wrong_type_fields"]:

        result["is_valid"] = False

        if "wrong_type" not in result["failure_modes"]:
            result["failure_modes"].append("wrong_type")

    return result


# ==========================================================
# ATTEMPT 1 PROMPT BUILDER
# ==========================================================

def build_attempt_1_prompt(task, schema):

    schema_str = "\n".join([
        f'  "{k}": {v.__name__}'
        for k, v in schema.items()
    ])

    return f"""
You are a structured data extraction system.

Respond with VALID JSON ONLY.

Rules:
- No explanation
- No markdown
- No extra text
- No ```json fences
- Output must match the schema exactly

Required JSON schema:
{{
{schema_str}
}}

Task:
{task}
""".strip()


# ==========================================================
# RETRY PROMPT BUILDER
# ==========================================================

def build_retry_prompt(
    original_task,
    invalid_output,
    validation_result,
    schema
):

    schema_str = "\n".join([
        f'  "{k}": {v.__name__}'
        for k, v in schema.items()
    ])

    # ------------------------------------------------------
    # SAFE SERIALIZATION
    # ------------------------------------------------------

    try:
        validation_str = json.dumps(
            validation_result,
            indent=2
        )

    except TypeError:
        validation_str = str(validation_result)

    return f"""
The previous response failed validation.

ORIGINAL TASK:
{original_task}

PREVIOUS INVALID OUTPUT:
{invalid_output}

VALIDATION FAILURES:
{validation_str}

REQUIRED JSON SCHEMA:
{{
{schema_str}
}}

Return ONLY valid JSON.
No explanation.
No markdown.
No extra text.
""".strip()


# ==========================================================
# MAIN PIPELINE
# ==========================================================

def generate_with_validation(
    model,
    task,
    schema,
    temperature=0.8
):

    # ------------------------------------------------------
    # BUILD ATTEMPT 1 PROMPT
    # ------------------------------------------------------

    structured_prompt = build_attempt_1_prompt(
        task=task,
        schema=schema
    )

    # ------------------------------------------------------
    # ATTEMPT 1
    # ------------------------------------------------------

    attempt_1 = benchmark_model(
    model,
    structured_prompt,
    temperature
)

    raw_response_1 = attempt_1["response"]

    validation_1 = validate_structured_response(
        raw_response_1,
        schema
    )

    attempt_1_result = {
        "original_task": task,
        "structured_prompt": structured_prompt,
        "raw_response": raw_response_1,
        "validation_result": validation_1,
        "latency": attempt_1.get("total_latency_seconds"),
        "token_count": attempt_1.get("token_count")
    }

    # ------------------------------------------------------
    # SUCCESS ON FIRST TRY
    # ------------------------------------------------------

    if validation_1["is_valid"]:

        return {
            "attempt_1_result": attempt_1_result,
            "attempt_2_result": None,
            "final_valid": True,
            "recovery": False,
            "final_output": validation_1["parsed"]
        }

    # ------------------------------------------------------
    # BUILD RETRY PROMPT
    # ------------------------------------------------------

    retry_prompt = build_retry_prompt(
        original_task=task,
        invalid_output=raw_response_1,
        validation_result=validation_1,
        schema=schema
    )

    # ------------------------------------------------------
    # ATTEMPT 2
    # ------------------------------------------------------

    attempt_2 = benchmark_model(
    model,
    retry_prompt,
    temperature
)

    raw_response_2 = attempt_2["response"]

    validation_2 = validate_structured_response(
        raw_response_2,
        schema
    )

    attempt_2_result = {
        "retry_prompt": retry_prompt,
        "raw_response": raw_response_2,
        "validation_result": validation_2,
        "latency": attempt_2.get("total_latency_seconds"),
        "token_count": attempt_2.get("token_count")
    }

    # ------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------

    recovery = (
        not validation_1["is_valid"]
        and validation_2["is_valid"]
    )

    final_valid = validation_2["is_valid"]

    final_output = (
        validation_2["parsed"]
        if validation_2["is_valid"]
        else None
    )

    return {
        "attempt_1_result": attempt_1_result,
        "attempt_2_result": attempt_2_result,
        "final_valid": final_valid,
        "recovery": recovery,
        "final_output": final_output
    }