#
# Copyright (c) 2026, Giridhar Narasimhamurthy. All rights reserved.
# Use is subject to license terms.
#

import yaml
from typing import List
from pydantic import BaseModel


class Requirement(BaseModel):
    category: str  # functional, nonfunctional
    criticality: str  # mandatory, optional
    description: str


class DesignDocument:
    def __init__(self):
        self.requirements: List[Requirement] = []

    def load_from_yaml(self, file_path: str):
        """
        Parses the YAML file and populates the requirements list.
        Expected YAML format:
        - [category, criticality, description]
        """
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        for item in raw_data.get("requirements", []):
            # Assumes format: ["functional", "mandatory", "description text"]
            if len(item) == 3:
                self.requirements.append(
                    Requirement(
                        category=item[0].strip().lower(),
                        criticality=item[1].strip().lower(),
                        description=item[2].strip(),
                    )
                )

    def generate_llm_requirements_list(self) -> str:
        """
        Serializes the requirements into a prioritized list for the LLM agent.
        Categorizes them to help the agent distinguish between hard constraints (SLAs)
        and soft preferences.
        """
        output = ["### BUSINESS DATA PROTECTION REQUIREMENTS ###", ""]

        # Group by category for better LLM reasoning
        for cat in ["functional", "nonfunctional"]:
            output.append(f"## {cat.upper()} REQUIREMENTS")

            # Sub-group by criticality (Mandatory first)
            for crit in ["mandatory", "optional"]:
                reqs = [
                    r
                    for r in self.requirements
                    if r.category == cat and r.criticality == crit
                ]
                if reqs:
                    output.append(f"  [{crit.upper()}]")
                    for r in reqs:
                        output.append(f"  - {r.description}")
            output.append("")

        return "\n".join(output)
