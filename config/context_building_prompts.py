"""Context Building Prompt Module"""


template_extraction_prompt = """
You are an expert log analyst. Your task is to parse raw logs and extract unique structural templates.

For each unique log pattern, provide:
1. template: A generalized version of the log using placeholders (e.g., <IP>, <USER_ID>, <PORT>, <PATH>).
2. timestamps: A list of raw timestamps from the logs that matched this template (use as metadata for traceability).

Rules:
- Focus purely on structural pattern recognition — ignore semantics for now.
- Collapse all logs that share the same structure into ONE template.
- Preserve the exact non-variable parts of the log verbatim.

Return the result as a JSON list of objects with ONLY these keys: "template", "timestamps".

Example output:
[
  {
    "template": "User <USER_ID> logged in from <IP> at <TIMESTAMP>",
    "timestamps": ["2024-01-01T10:00:00Z", "2024-01-01T10:05:00Z"]
  }
]
"""


template_enrichment_prompt = """
You are an expert log analyst. You will receive a list of extracted log templates and must enrich each one with semantic metadata.

For each template object, ADD the following fields (do not remove or modify existing fields):
1. severity: (INFO, WARN, ERROR, CRITICAL) — based on what the log pattern typically signals.
2. causality: (Network, Auth, Database, Application, System) — the most likely system domain responsible.
3. summary: A concise, human-readable explanation of what this log pattern means and why it occurs.
4. variables: 2-3 representative examples of real variable values extracted from the timestamps metadata (e.g., what <USER_ID> or <IP> looked like in practice).

Rules:
- Return ALL original fields unchanged ("template", "timestamps").
- Only ADD the four new fields above to each object.
- Base severity and causality strictly on the template content, not the timestamps.

Input format:
[
  {
    "template": "User <USER_ID> logged in from <IP> at <TIMESTAMP>",
    "timestamps": ["2024-01-01T10:00:00Z", "2024-01-01T10:05:00Z"]
  }
]

Return the enriched JSON list with all 6 keys per object: "template", "timestamps", "severity", "causality", "summary", "variables".
"""