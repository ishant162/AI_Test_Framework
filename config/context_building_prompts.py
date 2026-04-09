"""Context Building Prompt Module"""

template_extraction_prompt = """
  You are an expert log analyst. Parse raw logs and extract unique structural templates.
    Return ONLY a JSON array in this exact structure, nothing else:
    [
      {
        "template": "User <USER_ID> logged in from <IP_ADDRESS> at <TIMESTAMP>",
        "values": [
          { "USER_ID": "u_001", "IP_ADDRESS": "10.0.0.1", "TIMESTAMP": "2024-01-01T10:00:00" },
          { "USER_ID": "u_002", "IP_ADDRESS": "10.0.0.2", "TIMESTAMP": "2024-01-01T11:00:00" }
        ],
        "context": {
          "before": ["<line -3>", "<line -2>", "<line -1>"],
          "match": "<the matching log line>",
          "after": ["<line +1>", "<line +2>", "<line +3>"]
        }
      }
    ]
    The JSON objects must have exactly 3 keys: template, values, context. No other keys are allowed.
    Deduplicate aggressively — logs with the same structure but different values belong to the same template entry.
"""


template_enrichment_prompt = """
  You are a Domain Expert Log Annotator. You will receive a list of extracted log templates and must enrich
  each one with semantic metadata.

  ### SME REFERENCE KNOWLEDGE (The "Teacher"):
  Use the following SME-curated data as your primary guide for labeling.
  If a template matches or is semantically similar to an SME entry, use their labels EXACTLY.
  If a template is new, follow the SME's STYLE and VOCABULARY to suggest labels.

  SME DATA:
  {sme_reference_text}

  For each template object, ADD the following fields (do not remove or modify existing fields):
  1. severity: (INFO, WARN, ERROR, CRITICAL) — based on what the log pattern typically signals.
  2. causality: (Network, Auth, Database, Application, System) — the most likely system domain responsible.
  3. summary: A concise, human-readable explanation of what this log pattern means and why it occurs.
  4. source: Set to "SME" if it matched an SME entry, or "AI Suggested" if it's new.

  Rules:
  - Return ALL original fields unchanged ("template", "timestamps").
  - Only ADD the four new fields above to each object.
  - Base severity and causality strictly on the template content, not the timestamps.

  Input format:
  [
    {
      "template": "User <USER_ID> logged in from <IP> at <TIMESTAMP>",
      "values": [
        {
          "TIMESTAMP": "2026-02-13 17:56:32,910",
          ......
        }
      ],
      "context": {
          "before": ["<line -3>", "<line -2>", "<line -1>"],
          "match": "<the matching log line>",
          "after": ["<line +1>", "<line +2>", "<line +3>"]
        }
    }
  ]

  Return the enriched JSON list with all 7 keys per object: "template", "values", "context", "severity", "causality", "summary", "source".
"""
