"""Context Building Prompt Module"""

template_extraction_prompt = """Parse raw logs into unique structural templates.
Return ONLY a JSON array. Each object must have exactly these keys: "template", "values" (list of dicts), "context" (dict with "before", "match", "after").
Deduplicate aggressively by template structure.
Structure: [{"template": "...", "values": [{"VAR": "val"}], "context": {"before": [], "match": "", "after": []}}]"""


template_enrichment_prompt = """Enrich log templates with metadata. 
Also convert all SME entries in {sme_reference_text} into this format and include them in the output.

For each object, ADD:
1. severity: (INFO, WARN, ERROR, CRITICAL)
2. causality: (Network, Auth, Database, Application, System)
3. summary: Concise human explanation.
4. source: "SME" if matched, "AI Suggested" if new.

Rules:
- Keep original "template", "values", "context" unchanged.
- Base labels on template meaning.
- SME-derived templates must use: "values": [], "context": null.
- Return ONLY the enriched JSON array with 7 keys: template, values, context, severity, causality, summary, source."""


augmentation_prompt = """Generate 3-5 synthetic variations for each log template to expand the knowledge base.

Task:
1. Vary "values": Use diverse, plausible data for placeholders.
2. Vary "context": Create realistic "before", "match", and "after" lines.
3. Inject Knowledge: Add relevant error codes or system behaviors (e.g., AWS/Azure/CVE) where applicable.

Rules:
- Set "source" to "AI Augmented".
- Maintain original structure (7 keys).
- Return ONLY a valid JSON array of the new synthetic entries.
- Output format: [{"template": "...", "values": [...], "context": {...}, "severity": "...", "causality": "...", "summary": "...", "source": "AI Augmented"}]"""