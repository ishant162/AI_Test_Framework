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
  each one with semantic metadata. You must ALSO convert every SME template found inside
  sme_reference_text into the same enriched JSON object format and include them
  in the final output list.

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
  - Base severity and causality strictly on template meaning (not timestamps).
  - SME-derived templates must include "template", "values": [], "context": null.

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


augmentation_prompt = """
  You are an expert Log Data Augmentor. Your task is to generate synthetic, yet realistic, variations of provided log templates.
  This is crucial for expanding the knowledge base and improving the robustness of log analysis.

  ### Input:
  You will receive a JSON array of enriched log templates, each containing 'template', 'values', 'context', 'severity',
  'causality', 'summary', and 'source'.

  ### Task:
  For each provided template, generate 3-5 new, distinct synthetic log entries. These new entries should:
  1.  **Vary the 'values'**: Replace the placeholders in the 'template' with diverse, plausible data. For example,
  if a template has <USER_ID>, generate different user IDs.
  2.  **Vary the 'context'**: Create new 'before', 'match', and 'after' lines that realistically surround the synthetic log entry.
  This can include different timestamps, preceding/succeeding log messages, or related system events.
  3.  **Inject External Knowledge (if applicable)**: If the template suggests a common error, security event,
  or system behavior, subtly inject relevant external knowledge (e.g., common HTTP status codes, specific error messages from
  known systems like AWS, Azure, or common security vulnerability names like CVE-XXXX-XXXXX) into the synthetic log or its context.

  ### Output:
  Return ONLY a JSON array of the **augmented log templates**. Each object in the array should maintain the original structure but
  with updated 'values' and 'context' fields reflecting the synthetic data. Ensure the 'source' field for augmented data is set
  to "AI Augmented".

  Example of an augmented entry:
  [
    {
      "template": "User <USER_ID> logged in from <IP_ADDRESS> at <TIMESTAMP>",
      "values": [
        { "USER_ID": "u_003", "IP_ADDRESS": "192.168.1.10", "TIMESTAMP": "2024-01-01T12:00:00" },
        { "USER_ID": "u_004", "IP_ADDRESS": "172.16.0.5", "TIMESTAMP": "2024-01-01T13:00:00" }
      ],
      "context": {
        "before": ["[INFO] Starting authentication service", "[DEBUG] User u_003 attempting login"],
        "match": "User u_003 logged in from 192.168.1.10 at 2024-01-01T12:00:00",
        "after": ["[INFO] Session created for u_003", "[DEBUG] Redirecting to dashboard"]
      },
      "severity": "INFO",
      "causality": "Auth",
      "summary": "Successful user login event.",
      "source": "AI Augmented"
    }
  ]

  Ensure the output is a valid JSON array of augmented template objects.
"""
