## Why Structured Output Matters

Plain text requires the application to parse
natural language — fragile, breaks when phrasing
changes, impossible to reliably extract fields from.

JSON gives the application direct field access.
No parsing. No guessing. One line of code per field.

This is the difference between:
- Text: "The patient seems urgent" → how do you 
  trigger an alert from this?
- JSON: {"urgency": "high"} → if response["urgency"] 
  == "high": trigger_alert()

Structured output is not about formatting.
It is about making model output machine-readable.