#
# Copyright (c) 2026, Giridhar Narasimhamurthy. All rights reserved.
# Use is subject to license terms.
#

import yaml
import json
from typing import List, Tuple, Dict

"""
data_classification: maps resource_id to classification label
"""
class SystemMap:
    def __init__(self):
        self.hosts: List[str] = []
        self.apps: List[str] = []
        self.network_connections: List[Tuple[str, str]] = []
        self.data_storage: List[str] = []
        self.relationships: List[Tuple[str, str, str]] = []
        self.data_classification: Dict[str, str] = {}

    def load_from_yaml(self, file_path: str):
        """
        Reads IT infrastructure description and populates class members.
        Expects a YAML structure matching the class attributes.
        """
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.hosts = data.get('hosts', [])
        self.apps = data.get('apps', [])
        self.data_storage = data.get('data_storage', [])
        
        # Convert list of lists/dicts from YAML to Tuples for internal consistency
        self.network_connections = [tuple(conn) for conn in data.get('network_connections', [])]
        self.relationships = [tuple(rel) for rel in data.get('relationships', [])]
        self.data_classification = data.get('classification', {})

    def get_policy_suggestion(self, resource_id: str) -> List[str]:
        """
        Technical mapping of classification to protection methods 
        as per De Guise's standards.
        """
        tier = self.data_classification.get(resource_id, "Standard")
        
        mappings = {
            "Tier 1": ["Synchronous Replication", "Snapshots (15min)", "CDP (Continuous Data Protection)"],
            "Tier 2": ["Asynchronous Replication", "Daily Backup", "Off-site Copy"],
            "Tier 3": ["Weekly Backup", "Cloud Archive"],
            "PII/Regulated": ["Encryption at Rest", "Immutable Snapshots (WORM)", "Audit Logging"]
        }
        
        return mappings.get(tier, ["Standard Backup"])

    def generate_llm_context(self) -> str:
        """
        Updated descriptive structure including Data Classification.
        Links logical assets to protection tiers for LLM reasoning.
        """
        context_lines = ["### IT INFRASTRUCTURE SYSTEM MAP ###", ""]
        
        context_lines.append("## ASSETS & CLASSIFICATION")
        # List apps with their tiers
        app_list = []
        for app in self.apps:
            tier = self.data_classification.get(app, "Standard")
            app_list.append(f"{app} ({tier})")
        context_lines.append(f"- Applications: {', '.join(app_list)}")
        
        context_lines.append(f"- Hosts: {', '.join(self.hosts)}")
        
        # List storage with classification if applicable
        storage_list = []
        for ds in self.data_storage:
            tier = self.data_classification.get(ds, "Standard")
            storage_list.append(f"{ds} ({tier})")
        context_lines.append(f"- Storage Nodes: {', '.join(storage_list)}")
        context_lines.append("")

        context_lines.append("## DEPENDENCY & AVAILABILITY CHAINS")
        for app, host, storage in self.relationships:
            app_tier = self.data_classification.get(app, "Standard")
            storage_tier = self.data_classification.get(storage, "Standard")
            
            chain = (f"- SERVICE: {app} [Tier: {app_tier}] "
                     f"RUNS_ON {host} "
                     f"SAVES_TO {storage} [Tier: {storage_tier}]")
            context_lines.append(chain)
        
        context_lines.append("")
        context_lines.append("## NETWORK TOPOLOGY")
        for h1, h2 in self.network_connections:
            context_lines.append(f"- DUPLEX_LINK: {h1} <---> {h2}")

        context_lines.append("")
        context_lines.append("## PROTECTION POLICY MAPPINGS (Reference)")
        # Provide the LLM the "De Guise Standards" to map tiers to actions
        unique_tiers = set(self.data_classification.values())
        for tier in unique_tiers:
            methods = ", ".join(self.get_policy_suggestion_by_tier(tier))
            context_lines.append(f"- {tier}: {methods}")

        return "\n".join(context_lines)

    def get_policy_suggestion_by_tier(self, tier: str) -> List[str]:
        """Internal helper for the context generator."""
        mappings = {
            "Tier 1": ["Sync Replication", "15min Snapshots", "CDP"],
            "Tier 2": ["Async Replication", "Daily Backup"],
            "Tier 3": ["Weekly Backup", "Cloud Archive"],
            "PII/Regulated": ["Encryption", "Immutable WORM", "Audit"]
        }
        return mappings.get(tier, ["Standard Backup"])
