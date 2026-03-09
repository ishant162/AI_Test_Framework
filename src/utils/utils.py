import json
import re
from typing import Any, Dict, Optional


def extract_and_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract and parse JSON from a string that may contain markdown or extra text.
    """
    # 1. Try direct parsing first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try to find JSON block in markdown (```json ... ```)
    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Try to find anything between the first { and the last }
    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(1))
        except json.JSONDecodeError:
            pass

    return None