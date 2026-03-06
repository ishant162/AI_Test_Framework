import re
from typing import List, Dict, Any, Optional
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

class LogParser:
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize Drain3 TemplateMiner.
        """
        config = TemplateMinerConfig()
        # In newer versions of drain3, load_defaults() might not be needed or named differently.
        # Usually, the default constructor of TemplateMinerConfig already has defaults.
        
        self.template_miner = TemplateMiner(config=config)
        self.custom_regex_templates = []

    def add_custom_templates(self, regex_list: List[Dict[str, str]]):
        """
        Add user-defined regex templates for priority extraction.
        Each dict should have 'regex' and 'label' keys.
        """
        for item in regex_list:
            self.custom_regex_templates.append({
                "pattern": re.compile(item['regex']),
                "label": item['label']
            })

    def parse_logs(self, log_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse log lines and extract templates.
        Returns a list of unique templates with their metadata.
        """
        extracted_templates = {}

        for line in log_lines:
            line = line.strip()
            if not line:
                continue

            # 1. Check custom regex templates first (Priority)
            matched_custom = False
            for custom in self.custom_regex_templates:
                if custom['pattern'].search(line):
                    template_str = custom['label']
                    if template_str not in extracted_templates:
                        extracted_templates[template_str] = {
                            "template": template_str,
                            "source": "custom_regex",
                            "count": 1,
                            "examples": [line[:200]]
                        }
                    else:
                        extracted_templates[template_str]["count"] += 1
                        if len(extracted_templates[template_str]["examples"]) < 3:
                            extracted_templates[template_str]["examples"].append(line[:200])
                    matched_custom = True
                    break
            
            if matched_custom:
                continue

            # 2. Use Drain3 for automated template extraction
            result = self.template_miner.add_log_message(line)
            template_id = result.get("cluster_id")
            template_str = result.get("template_mined")

            if template_id not in extracted_templates:
                extracted_templates[template_id] = {
                    "template": template_str,
                    "source": "drain3",
                    "count": 1,
                    "examples": [line[:200]]
                }
            else:
                extracted_templates[template_id]["count"] += 1
                if len(extracted_templates[template_id]["examples"]) < 3:
                    extracted_templates[template_id]["examples"].append(line[:200])

        return list(extracted_templates.values())

# Test with example logs
if __name__ == "__main__":
    parser = LogParser()
    parser.add_custom_templates([
        {"regex": r"User \d+ failed login", "label": "USER_LOGIN_FAILURE"}
    ])
    
    sample_logs = [
        "2023-10-01 10:00:01 INFO Connected to database at 192.168.1.1:5432",
        "2023-10-01 10:00:02 INFO Connected to database at 192.168.1.2:5432",
        "2023-10-01 10:00:05 ERROR User 123 failed login from 10.0.0.5",
        "2023-10-01 10:00:10 WARN Disk usage at 90% on /dev/sda1",
        "2023-10-01 10:00:15 WARN Disk usage at 95% on /dev/sdb1"
    ]
    
    templates = parser.parse_logs(sample_logs)
    for t in templates:
        print(f"Source: {t['source']} | Template: {t['template']} | Count: {t['count']}")
